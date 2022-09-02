import re

from lxml import etree
from inspect import Signature, Parameter

from sdRDM.tools.utils import snake_to_camel
from sdRDM.base.listplus import ListPlus

class IDGenerator:
    def __init__(self, pattern: str):
        self.pattern = pattern.replace(r"\d", "INDEX")
        self.index = 0
    
    def __call__(self):
        return self.generate_id()
    
    def generate_id(self):
        id = re.sub(r"\[?INDEX\]?[+|*|?]?", str(self.index), self.pattern)
        self.index += 1
        return id

def build_xml(obj, pascal: bool = True):
    node = etree.Element(snake_to_camel(obj.__class__.__name__, pascal=pascal),  attrib={}, nsmap={})

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
                    composite_node.append(build_xml(sub_obj, pascal=pascal))
                
                if len(composite_node) > 0:
                    node.append(composite_node)    
                
            else:
                if _is_empty(value):
                    continue
                
                node.append(build_xml(value, pascal=pascal))

        elif isinstance(value, ListPlus):
            # Turn lists of native types into sub-elements
            composite_node = etree.Element(xml_option, attrib={}, nsmap={})
            
            if not value:
                # Skip empty lists
                continue

            for v in value:
                try:
                    element = etree.Element(
                        xml_option, attrib={}, nsmap={}
                    )
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
    