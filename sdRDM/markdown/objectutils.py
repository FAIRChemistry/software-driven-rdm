import re

from markdown_it.token import Token
from typing import List, Dict

from sdRDM.markdown.tokens import MarkdownTokens

OPTION_PATTERN = r"\s*([A-Za-z0-9\_]*)\s*\:\s*(.*)"
LINKED_TYPE_PATTERN = r"\[([A-Za-z0-9\_]*)\]\(\#[A-Za-z0-9\_]*\)"
REFERENCE_TYPE_PATTERN = r"\@([A-Za-z0-9\_]*).([A-Za-z0-9\_]*)"

TAG_MAPPING = {
    "h1": MarkdownTokens.MODULE,
    "h2": MarkdownTokens.HEADING,
    "h3": MarkdownTokens.OBJECT,
    "p": MarkdownTokens.DESCRIPTION,
}


def parse_markdown_module(name: str, module: List[Token]) -> List[Dict]:
    """Parses the part of a markdown model that follows after an H2 heading"""

    TOKEN_MAPPING = {
        MarkdownTokens.OBJECT: process_object,
        MarkdownTokens.DESCRIPTION: process_description,
        MarkdownTokens.ATTRIBUTE: process_attribute,
        MarkdownTokens.OPTION: process_option,
        MarkdownTokens.HEADING: lambda element, object_stack: None,
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

        TOKEN_MAPPING[token](element=element, object_stack=object_stack)

    return add_module_name_to_objects(name, object_stack)


def add_module_name_to_objects(name: str, object_stack: List[Dict]) -> List[Dict]:
    """Adds the module name to all objects for directory construction"""

    for obj in object_stack:
        obj["module"] = name

    return object_stack


def process_object(element: Token, object_stack: List) -> None:
    """Processes a new object and adds it to the object stack"""

    assert element.children is not None, "Object has no children"

    object_stack.append(
        {
            "name": get_object_name(element.children),
            "docstring": "",
            "attributes": [],
            "type": "object",
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


def process_description(element: Token, object_stack: List) -> None:
    """Processes a description and adds it to the recent object"""

    if object_stack == []:
        return

    object_stack[-1]["docstring"] += element.content


def process_attribute(element: Token, object_stack: List) -> None:
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


def process_option(element: Token, object_stack: List) -> None:
    """Processes a new option and adds it to the recent attribute of the recent object"""

    match = re.match(OPTION_PATTERN, element.content)

    assert match is not None, f"Option '{element.content}' is not valid."

    option, value = match.groups()

    if option.lower().strip() == "type":
        value = process_type_option(value, object_stack)

    object_stack[-1]["attributes"][-1][option.strip().lower()] = value


def process_type_option(dtypes: str, object_stack: List) -> List[str]:
    """Processes the specific type option and extracts references as well as multiple types"""

    processed_types = []

    for dtype in dtypes.split(","):
        dtype = dtype.strip()

        if is_linked_type(dtype):
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


def is_linked_type(dtype: str) -> bool:
    """Checks whether the given type is a markdown link"""
    return bool(re.match(LINKED_TYPE_PATTERN, dtype))


def is_reference_type(dtype: str) -> bool:
    """Checks whether the given type is an attribute reference"""
    return bool(re.match(REFERENCE_TYPE_PATTERN, dtype))
