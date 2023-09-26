import re
from lxml import etree
from lxml.etree import _Element, QName
from typing import Any, Dict, Tuple, List, IO, get_origin

from sdRDM.tools.utils import snake_to_camel
from sdRDM.base.listplus import ListPlus


# ! Reader
def read_xml(xml_string: bytes, object: "DataModel") -> Dict:
    """Parses a given XML file or StringIO to a a dictionary

    This function closely operates with the given data model
    and inferes types and general structural information from
    the model.
    """

    root = etree.fromstring(xml_string)  # type: ignore
    library = gather_object_types(object)

    return parse_xml_element_to_model(library, root)


def gather_object_types(obj) -> Dict:
    """Gets all sub types found in a"""

    objects = {obj.__name__: obj}

    for field in obj.__fields__.values():
        if hasattr(field.type_, "__fields__"):
            subobject = field.type_
            objects[subobject.__name__] = subobject
            objects.update(
                {**gather_object_types(subobject), subobject.__name__: subobject}
            )

    return objects


def parse_xml_element_to_model(library: Dict, element: _Element) -> Dict:
    cls = library[QName(element).localname]
    attributes, alias_map, objects = prepare_xml_parsing(cls)

    for subelement in element:  # type: ignore
        # Go through each element and add it to the attributes
        map_xml_element(attributes, subelement, alias_map, library, objects)

    for name, value in element.attrib.items():
        attributes[name] = value

    return attributes


def prepare_xml_parsing(object: "DataModel") -> Tuple[Dict, Dict, List[str]]:
    """Retrieves attributes and preparse parsing of an XML object"""

    attributes = {}
    alias_map = {}
    objects = []

    # Prepare for expected attributes
    for name, attr in object.__fields__.items():
        is_multiple = get_origin(attr.outer_type_) == list
        is_object = hasattr(attr.type_, "__fields__")

        alias_map[name] = name

        if is_object and is_multiple:
            attributes[name] = []
            objects.append(name)
        elif is_object and not is_multiple:
            attributes[name] = None
            alias_map[attr.type_.__name__] = name
            objects.append(name)
        elif not is_object and is_multiple:
            attributes[name] = []
        else:
            attributes[name] = None

        if "xml" in attr.field_info.extra:
            # Overrides all other things
            alias_map[attr.field_info.extra["xml"].replace("@", "")] = name

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
    node = etree.Element(
        snake_to_camel(obj.__class__.__name__, pascal=pascal), attrib={}, nsmap={}
    )

    for name, field in obj.__fields__.items():
        value = obj.__dict__[name]

        if _is_none(value):
            # Skip None and empty values
            continue

        dtype = field.type_
        outer = field.outer_type_
        xml_option = _convert_multiple_tag_options(
            field.field_info.extra.get("xml"),
            value,
        )

        if not xml_option:
            # If not specified in Markdown
            xml_option = snake_to_camel(name, pascal=pascal)

        # Process outer to be parsed
        if hasattr(outer, "__origin__"):
            outer = outer.__origin__.__name__

        if hasattr(dtype, "__fields__") or hasattr(value, "__fields__"):
            # Trigger recursion if a complex type
            # is encountered --> Creates a sub node

            if outer == "list":
                if xml_option == value[0].__class__.__name__:
                    composite_node = node
                    is_parent = True
                else:
                    composite_node = etree.Element(xml_option, attrib={}, nsmap={})
                    is_parent = False

                for sub_obj in value:
                    composite_node.append(write_xml(sub_obj, pascal=pascal))

                if len(composite_node) > 0 and not is_parent:
                    node.append(composite_node)

            else:
                if _is_empty(value):
                    continue

                node.append(write_xml(value, pascal=pascal))

        elif isinstance(value, ListPlus):
            # Turn lists of native types into sub-elements
            composite_node = etree.Element(xml_option, attrib={}, nsmap={})

            if not value:
                # Skip empty lists
                continue

            for v in value:
                try:
                    element = etree.Element(xml_option, attrib={}, nsmap={})
                except KeyError:
                    element = etree.Element(xml_option, attrib={}, nsmap={})
                element.text = str(v)
                node.append(element)

        else:
            # Process single value and make sure attributes are properly added
            if xml_option.startswith("@"):
                node.attrib[xml_option.replace("@", "")] = str(value)
            else:
                element = etree.Element(xml_option, attrib={}, nsmap={})
                element.text = str(value)
                node.append(element)

    return node


def _is_empty(value):
    """Checks whether a given class object is completely empty"""
    values = value.dict(exclude={"id", "__source__"}, exclude_none=True)
    return not any([key for key, v in values.items() if v])


def _is_none(value):
    if isinstance(value, (ListPlus, list)) and len(value) == 0:
        return True

    if value is None:
        return True

    return False


def _convert_multiple_tag_options(options: str, value: Any):
    """Checks, whether there are multiple options for a tag, by native types"""

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
    """Extracts the type of all entries within a list. If there are multiple, an excpetion is raised

    !! This function will be extended to the mixed case, at some point.
    """

    dtypes = set([v.__class__.__name__ for v in values])

    if len(dtypes) > 1:
        raise TypeError(
            f"Multiple types found in {values} - Cannot export to XML by options"
        )

    return dtypes.pop()
