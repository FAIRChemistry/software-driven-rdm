from lxml import etree
from sdRDM.tools.utils import snake_to_camel
from sdRDM.base.listplus import ListPlus


def write_xml(obj, pascal: bool = True):
    node = etree.Element(
        snake_to_camel(obj.__class__.__name__, pascal=pascal), attrib={}, nsmap={}
    )

    for name, field in obj.__fields__.items():
        dtype = field.type_
        outer = field.outer_type_
        xml_option = field.field_info.extra.get("xml")
        value = obj.__dict__[name]

        if value is None:
            # Skip None values
            continue

        if not xml_option:
            # If not specified in Markdown
            xml_option = snake_to_camel(name, pascal=pascal)

        # Process outer to be parsed
        if hasattr(outer, "__origin__"):
            outer = outer.__origin__.__name__

        if hasattr(dtype, "__fields__"):
            # Trigger recursion if a complex type
            # is encountered --> Creates a sub node

            if outer == "list":
                composite_node = etree.Element(xml_option, attrib={}, nsmap={})
                for sub_obj in value:
                    composite_node.append(write_xml(sub_obj, pascal=pascal))

                if len(composite_node) > 0:
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
                composite_node.append(element)

            node.append(composite_node)

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
