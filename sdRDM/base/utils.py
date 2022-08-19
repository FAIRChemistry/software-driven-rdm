from lxml import etree
from inspect import Signature, Parameter

from sdRDM.tools.utils import snake_to_camel


def build_xml(obj):
    node = etree.Element(snake_to_camel(obj.__class__.__name__))

    for name, field in obj.__fields__.items():
        dtype = field.type_
        outer = field.outer_type_

        # Process outer to be parsed
        if hasattr(outer, "__origin__"):
            outer = outer.__origin__.__name__

        if hasattr(dtype, "__fields__"):
            # Trigger recursion if a complex type
            # is encountered --> Creates a sub node
            composite_node = etree.Element(snake_to_camel(name))

            if outer == "list":
                for sub_obj in obj.__dict__[name]:
                    composite_node.append(build_xml(sub_obj))
            else:
                composite_node.append(build_xml(obj.__dict__[name]))

            node.append(composite_node)

        else:
            # Process primitive fields
            value = obj.__dict__[name]
            xml_option = field.field_info.extra.get("xml")

            if not xml_option:
                # If not specified in Markdown
                xml_option = name

            if isinstance(value, list):
                # Turn lists of native types into sub-elements
                composite_node = etree.Element(snake_to_camel(name))

                for v in value:
                    try:
                        element = etree.Element(
                            snake_to_camel(field.field_info.extra["xml"])
                        )
                    except KeyError:
                        element = etree.Element(snake_to_camel(name))
                    element.text = str(v)
                    composite_node.append(element)

                node.append(composite_node)

            else:
                # Process single value and make sure attributes are properly added
                if xml_option.startswith("@"):
                    node.attrib[xml_option.replace("@", "")] = str(obj.__dict__[name])
                else:
                    element = etree.Element(snake_to_camel(xml_option))
                    element.text = str(obj.__dict__[name])
                    node.append(element)

    return node

def forge_signature(cls):
    """Changes the signature of a class to include forbidden names such as 'yield'.
    
    Since PyDantic aliases are also applied to the signature, forbidden names
    such as 'yield' are impossible. This decorator will turn add an underscore
    while the exports aligns to the alias.
    
    """
        
    parameters = _construct_signature(cls)
    cls.__signature__ = Signature(parameters=parameters)
        
    return cls

def _construct_signature(cls):
    """Helper function to extract parameters"""
    
    parameters = []
    
    for name, parameter in cls.__signature__.parameters.items():

        if f"{name}_" in cls.__fields__:
            name = f"{name}_"

        parameters.append(Parameter(
            name=name,
            kind=parameter.kind,
            default=parameter.default,
            annotation=parameter.annotation
        ))
        
    return parameters
    