import re

from markdown_it.token import Token
from typing import List, Dict, Tuple
from sdRDM.markdown.smalltypes import process_small_type

from sdRDM.tools.utils import snake_to_camel
from sdRDM.markdown.tokens import MarkdownTokens

OPTION_PATTERN = r"\s*([A-Za-z0-9\_]*)\s*\:\s*(.*)"
LINKED_TYPE_PATTERN = r"\[([A-Za-z0-9\_]*)\]\(\#[A-Za-z0-9\_\-]*\)"
REFERENCE_TYPE_PATTERN = r"\@([A-Za-z0-9\_]*).([A-Za-z0-9\_]*)"

TAG_MAPPING = {
    "h1": MarkdownTokens.MODULE,
    "h2": MarkdownTokens.HEADING,
    "h3": MarkdownTokens.OBJECT,
    "p": MarkdownTokens.DESCRIPTION,
}


def parse_markdown_module(
    name: str, module: List[Token], external_types: Dict[str, "MarkdownParser"]
) -> List[Dict]:
    """Parses the part of a markdown model that follows after an H2 heading"""

    TOKEN_MAPPING = {
        MarkdownTokens.OBJECT: process_object,
        MarkdownTokens.DESCRIPTION: process_description,
        MarkdownTokens.ATTRIBUTE: process_attribute,
        MarkdownTokens.OPTION: process_option,
        MarkdownTokens.HEADING: lambda **kwargs: None,
    }

    object_stack = []

    for index, element in enumerate(module):
        if not element.content:
            continue

        if element.level == 1:
            token = TAG_MAPPING[module[index - 1].tag]
        elif element.level == 3:
            token = MarkdownTokens.ATTRIBUTE
        elif element.level > 3:
            token = MarkdownTokens.OPTION
        else:
            continue

        TOKEN_MAPPING[token](
            element=element, object_stack=object_stack, external_types=external_types
        )

    return add_module_name_to_objects(name, object_stack)


def add_module_name_to_objects(name: str, object_stack: List[Dict]) -> List[Dict]:
    """Adds the module name to all objects for directory construction"""

    for obj in object_stack:
        obj["module"] = name

    return object_stack


def process_object(element: Token, object_stack: List, **kwargs) -> None:
    """Processes a new object and adds it to the object stack"""

    assert element.children is not None, "Object has no children"

    object_stack.append(
        {
            "name": get_object_name(element.children),
            "docstring": "",
            "attributes": [],
            "type": "object",
            "subtypes": [],
        }
    )

    if has_parent(element.children):
        object_stack[-1]["parent"] = get_parent(element.children)


def get_object_name(children: List[Token]) -> str:
    """Gets the name of an object"""
    return children[0].content.replace("[", "").strip()


def has_parent(children: List[Token]) -> bool:
    """Checks whether an object inherits from another one"""
    return any(element.level == 1 for element in children)


def get_parent(children: List[Token]) -> str:
    """Gets the parent of an object"""
    return next(
        filter(lambda element: element.level == 1 and element.type == "text", children)
    ).content


def process_description(element: Token, object_stack: List, **kwargs) -> None:
    """Processes a description and adds it to the recent object"""

    if object_stack == []:
        return

    object_stack[-1]["docstring"] += element.content


def process_attribute(element: Token, object_stack: List, **kwargs) -> None:
    """Proceses a new attribute and adds it to the most recent object"""

    assert element.children, f"Element {element.content} has no children"

    attribute = {
        "name": get_attribute_name(element.children),
        "required": is_required(element.children),
    }

    if not is_required(element.children):
        attribute["default"] = None

    object_stack[-1]["attributes"].append(attribute)


def is_required(children: List[Token]) -> bool:
    """Checks whether an attribute is required by if a bold is in its children"""

    return any(element.tag == "strong" for element in children)


def get_attribute_name(children: List[Token]) -> str:
    """Retrieves the name of an attribute"""

    return next(
        filter(lambda element: element.type == "text" and element.content, children)
    ).content


def process_option(
    element: Token,
    object_stack: List,
    external_types: Dict[str, "MarkdownParser"],
    **kwargs,
) -> None:
    """Processes a new option and adds it to the recent attribute of the recent object"""

    match = re.match(OPTION_PATTERN, element.content)

    assert match is not None, f"Option '{element.content}' is not valid."

    option, value = match.groups()

    if option.lower().strip() == "type":
        value = process_type_option(value, object_stack, external_types)
    elif option.lower().strip() == "multiple" and attribute_has_default(object_stack):
        del object_stack[-1]["attributes"][-1]["default"]
        object_stack[-1]["attributes"][-1]["default_factory"] = "ListPlus()"

    object_stack[-1]["attributes"][-1][option.strip().lower()] = value


def attribute_has_default(object_stack: List[Dict]) -> bool:
    """Checks whether the current attribute has a default value or not"""
    return "default" in object_stack[-1]["attributes"][-1]


def process_type_option(
    dtypes: str, object_stack: List, external_types: Dict[str, "MarkdownParser"]
) -> List[str]:
    """Processes the specific type option and extracts references as well as multiple types"""

    processed_types = []

    if has_small_type(dtypes):
        small_type = process_small_type(dtypes, object_stack)
        object_stack[-1]["subtypes"].append(small_type)

        # Update dtypes and add the small type to the processed types
        dtypes = re.sub(r"\{.*\}", "", dtypes).strip(",")
        processed_types.append(small_type["name"])

        # Set small type as default
        current_attr = object_stack[-1]["attributes"][-1]
        current_attr["default_factory"] = f"{small_type['name']}"

        del current_attr["default"]

    for dtype in dtypes.split(","):
        dtype = dtype.strip()

        if not dtype:
            continue

        if is_remote_type(dtype):
            dtype, cls_defs, url = process_remote_type(dtype)
            external_types[url] = cls_defs
        elif is_linked_type(dtype):
            dtype = re.sub(LINKED_TYPE_PATTERN, r"\1", dtype)
        elif is_reference_type(dtype):
            match = re.match(REFERENCE_TYPE_PATTERN, dtype)

            assert (
                match is not None
            ), f"Type '{dtype}' appears to be a reference, but has wrong syntax."

            dtype, attribute = match.groups()
            object_stack[-1]["attributes"][-1]["reference"] = f"{dtype}.{attribute}"

        processed_types.append(dtype)

    return processed_types


def is_remote_type(dtype: str) -> bool:
    """Checks whether the given type points to a remote model"""
    return "@" in dtype and "github" in dtype


def has_small_type(dtype: str) -> bool:
    # Pattern is {name: type, name: type, ...}
    pattern = r"\{.*\}"
    return bool(re.match(pattern, dtype))


def is_linked_type(dtype: str) -> bool:
    """Checks whether the given type is a markdown link"""
    return bool(re.match(LINKED_TYPE_PATTERN, dtype))


def is_reference_type(dtype: str) -> bool:
    """Checks whether the given type is an attribute reference"""
    return bool(re.match(REFERENCE_TYPE_PATTERN, dtype))


def process_remote_type(dtype: str) -> Tuple[str, Dict, str]:
    """Processes a remote type and adds it to the parsers external types

    Returns:
        (str): Name of the extracted object
        (str): Class definitions of the attached model
        (str): Remote URL of the the attached data model
    """

    from sdRDM.tools.gitutils import build_library_from_git_specs

    url, obj = dtype.split("@")

    cls_defs = build_library_from_git_specs(url=url, tmpdirname=obj, only_classes=True)

    objects_to_keep = gather_objects_to_keep(obj, cls_defs.objects)
    cls_defs.objects = list(
        filter(lambda obj: obj["name"] in objects_to_keep, cls_defs.objects)
    )

    return obj, cls_defs, url


def gather_objects_to_keep(name, objs, objects_to_keep=[]):
    """Traverse a data model and extracts a list of objects to keep.

    This function is intended to use in conjunction with nested data models
    that are referencing a remote repository. Here, only parts of the model
    need to be extracted that the object of interest requires.
    """

    try:
        # Get the dtype from the objects, if given
        obj = next(filter(lambda obj: obj["name"] == name, objs))
        objects_to_keep.append(name)

        if "parent" in obj:
            objects_to_keep.append(obj["parent"])

    except StopIteration:
        return

    # Gather all dtypes within this object
    all_dtypes = _get_attribute_dtypes(obj["attributes"])

    for dtype in all_dtypes:
        gather_objects_to_keep(dtype, objs, objects_to_keep)

    return objects_to_keep


def _get_attribute_dtypes(attributes):
    return set([dtype for attribute in attributes for dtype in attribute["type"]])
