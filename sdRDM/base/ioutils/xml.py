import re
from lxml import etree
from lxml.etree import _Element, QName
from typing import Any, Dict, Tuple, List, IO, get_args, get_origin

from sdRDM.tools.utils import snake_to_camel
from sdRDM.base.listplus import ListPlus


# ! Reader
def read_xml(xml_string: bytes, object: "DataModel") -> Dict:
    """Parses a given XML file or StringIO to a dictionary.

    Args:
        xml_string (bytes): The XML content as bytes.
        object (DataModel): The data model object.

    Returns:
        Dict: The parsed XML content as a dictionary.
    """
    root = etree.fromstring(xml_string)  # type: ignore
    library = gather_object_types(object)

    return parse_xml_element_to_model(library, root)


def gather_object_types(obj) -> Dict:
    """Gets all sub types found in an object.

    Args:
        obj: The object to gather sub types from.

    Returns:
        A dictionary containing the sub types found in the object.
    """

    objects = {obj.__name__: obj}

    for field in obj.model_fields.values():
        inners = get_args(field.annotation)

        for inner in inners:
            if hasattr(inner, "model_fields"):
                objects[inner.__name__] = inner
                objects.update(
                    {
                        **gather_object_types(inner),
                        inner.__name__: inner,
                    }
                )

    return objects


def parse_xml_element_to_model(library: Dict, element: _Element) -> Dict:
    """
    Parses an XML element into a model dictionary.

    Args:
        library (Dict): A dictionary containing the mapping of element names to model classes.
        element (_Element): The XML element to be parsed.

    Returns:
        Dict: A dictionary representing the parsed attributes of the XML element.
    """

    cls = library[QName(element).localname]
    attributes, alias_map, objects = prepare_xml_parsing(cls)

    for subelement in element:  # type: ignore
        # Go through each element and add it to the attributes
        map_xml_element(
            attributes,
            subelement,
            alias_map,
            library,
            objects,
        )

    for name, value in element.attrib.items():
        attributes[name] = value

    return attributes


def prepare_xml_parsing(object: "DataModel") -> Tuple[Dict, Dict, List[str]]:
    """
    Retrieves attributes and preparse parsing of an XML object.

    Args:
        object (DataModel): The XML object to be parsed.

    Returns:
        Tuple[Dict, Dict, List[str]]: A tuple containing the attributes dictionary, alias map dictionary, and a list of objects.

    """

    attributes = {}
    alias_map = {}
    objects = []

    # Prepare for expected attributes
    for name, attr in object.model_fields.items():
        inners = get_args(attr.annotation)
        extra = attr.json_schema_extra
        is_multiple = get_origin(attr.annotation) == list
        is_object = all([hasattr(inner, "model_fields") for inner in inners])

        if is_object:
            alias_map.update({inner.__name__: name for inner in inners})

        if extra and "xml" in extra:
            xml_option = extra["xml"]
            alias_map[xml_option.replace("@", "")] = name
        else:
            alias_map[name] = name

        if is_object and is_multiple:
            attributes[name] = []
            objects.append(name)
        elif is_object and not is_multiple:
            attributes[name] = None
            alias_map[attr.annotation.__name__] = name
            objects.append(name)
        elif not is_object and is_multiple:
            attributes[name] = []
        else:
            attributes[name] = None

    return attributes, alias_map, objects


def map_xml_element(
    attributes: Dict,
    element: _Element,
    alias_map: Dict,
    library: Dict,
    objects: List[str],
) -> None:
    """Parses a sub element found in an XML document and maps it accordingly to the data model"""

    if element.tag is etree.Comment:
        return

    attr_name = alias_map[element.tag]
    is_multiple = isinstance(attributes[attr_name], list)
    is_object = attr_name in objects

    if is_object and not is_multiple:
        attributes[attr_name] = parse_xml_element_to_model(library, element)
    elif is_object and is_multiple:
        attributes[attr_name] += [
            parse_xml_element_to_model(library, subelement) for subelement in element
        ]
    elif not is_object and is_multiple:
        attributes[attr_name] += [element.text]
    else:
        attributes[attr_name] = element.text


# ! Writer
def write_xml(obj, pascal: bool = True):
    """
    Converts an object to an XML element.

    Args:
        obj: The object to convert.
        pascal: A boolean indicating whether to use PascalCase for XML element names.
                If False, snake_case will be used.

    Returns:
        The XML element representing the object.
    """

    node = etree.Element(
        snake_to_camel(obj.__class__.__name__, pascal=pascal),
        attrib={},
        nsmap={},
    )

    for name, field in obj.model_fields.items():
        # Extract types and values
        value = getattr(obj, name)
        dtype = field.annotation
        outer = get_origin(dtype)
        inners = get_args(dtype)
        extra = field.json_schema_extra

        # Create boolean checks
        is_multiple = outer == list
        is_object = any([hasattr(inner, "model_fields") for inner in inners])

        # Exit if the value is None or empty
        if _is_none(value):
            continue
        elif is_object and _is_empty(value, is_multiple):
            continue

        # Handle XML options
        if extra is None or "xml" not in extra:
            xml_option = name
        else:
            xml_option = _convert_multiple_tag_options(
                extra.get("xml"),
                value,
            )

        if is_multiple and is_object:
            _handle_multiple_objects(
                value=value,
                xml_option=xml_option,
                node=node,
                pascal=pascal,
            )
        elif is_multiple and not is_object:
            _handle_multiple_base_types(
                value=value,
                xml_option=xml_option,
                node=node,
            )
        elif not is_multiple and is_object:
            node.append(write_xml(value, pascal=pascal))
        else:
            _handle_single_base_type(
                value=value,
                xml_option=xml_option,
                node=node,
            )

    return node


def _handle_multiple_objects(
    value: List["DataModel"],
    xml_option: str,
    node: etree.Element,
    pascal: bool,
):
    """
    Handles multiple objects in XML serialization.

    Args:
        value (List[DataModel]): The list of objects to be serialized.
        xml_option (str): The XML option for the composite node.
        node (etree.Element): The parent node to which the composite node will be appended.
        pascal (bool): Flag indicating whether to use PascalCase for XML element names.

    Returns:
        None
    """
    if xml_option == value[0].__class__.__name__:
        composite_node = node
        is_parent = True
    else:
        composite_node = etree.Element(xml_option, attrib={}, nsmap={})
        is_parent = False

    for entry in value:
        composite_node.append(write_xml(entry, pascal=pascal))

    if len(composite_node) > 0 and not is_parent:
        node.append(composite_node)


def _handle_multiple_base_types(
    value: List[Any],
    xml_option: str,
    node: etree.Element,
):
    """
    Handles multiple values in XML serialization.

    Args:
        value (List[Any]): The list of values to be serialized.
        xml_option (str): The XML option for the composite node.
        node (etree.Element): The parent node to which the composite node will be appended.

    Returns:
        None
    """

    for entry in value:
        element = etree.Element(xml_option, attrib={}, nsmap={})
        element.text = str(entry)
        node.append(element)


def _handle_single_base_type(
    value: List["DataModel"],
    xml_option: str,
    node: etree.Element,
):
    """
    Handles single base types in XML serialization.

    Args:
        value (List[DataModel]): The list of base type values to be serialized.
        xml_option (str): The XML option for the element.
        node (etree.Element): The parent node to which the element will be appended.

    Returns:
        None
    """

    if value is None:
        return
    if isinstance(value, bool):
        value = str(value).lower()  # type: ignore

    if xml_option.startswith("@"):
        node.attrib[xml_option.replace("@", "")] = str(value)
    else:
        element = etree.Element(xml_option, attrib={}, nsmap={})
        element.text = str(value)

        node.append(element)


def _is_empty(value, is_multiple: bool):
    """Checks whether a given class object is completely empty

    Args:
        value: The value to check for emptiness.
        is_multiple: A boolean indicating whether the value is a single object or a list of objects.

    Returns:
        bool: True if the value is empty, False otherwise.
    """

    if not is_multiple:
        value = [value]

    return all([_is_empty_single(v) for v in value])


def _is_empty_single(value):
    values = value.dict(exclude={"id", "__source__"}, exclude_none=True)
    return not any([key for key, v in values.items() if v])


def _is_none(value):
    """
    Check if a value is None or an empty list.

    Args:
        value: The value to be checked.

    Returns:
        bool: True if the value is None or an empty list, False otherwise.
    """
    if isinstance(value, (ListPlus, list)) and len(value) == 0:
        return True

    if value is None:
        return True

    return False


def _convert_multiple_tag_options(options: str, value: Any):
    """Checks, whether there are multiple options for a tag, by native types

    Args:
        options (str): The options for the tag.
        value (Any): The value to check the options against.

    Returns:
        str: The selected option based on the value's type.

    Raises:
        TypeError: If the value's type is not found in the options.

    """
    if not options:
        return None
    elif not bool(re.match(r"^\{.*\}$", options)):
        return options

    if isinstance(value, ListPlus):
        dtype = _extract_common_list_type(value)
    else:
        dtype = value.__class__.__name__

    splitted = options.rstrip("}").lstrip("{").split(",")
    mappings = {
        option.split(":")[0].strip(): option.split(":")[1].strip()
        for option in splitted
    }

    if dtype not in mappings:
        raise TypeError(f"Type {dtype} not found in {options} for {value}")

    return mappings[dtype]


def _extract_common_list_type(values: ListPlus) -> str:
    """Extracts the type of all entries within a list. If there are multiple, an exception is raised.

    Args:
        values (ListPlus): The list of values to extract the common type from.

    Returns:
        str: The common type of all entries in the list.

    Raises:
        TypeError: If there are multiple types found in the list.

    !! This function will be extended to the mixed case, at some point.
    """

    dtypes = set([v.__class__.__name__ for v in values])

    if len(dtypes) > 1:
        raise TypeError(
            f"Multiple types found in {values} - Cannot export to XML by options"
        )

    return dtypes.pop()
