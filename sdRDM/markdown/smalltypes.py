import re
from typing import Dict, List
from sdRDM.generator.datatypes import DataTypes
from sdRDM.tools.utils import snake_to_camel


def process_small_type(dtypes: str, object_stack: List[Dict]):
    """Processes small types of form {name: type, ...} to a valid object

    So called small types can be added to the sdRDM markdown syntax
    by using the following syntax:

        - attribute
            - name: {name: type, name: type, ...}

    This way no extra object (l3 heading) has to be defined for a small
    type that will most likely stay this way.

    """

    small_type = re.match(r"\{(.*)\}", dtypes).groups()[0]
    attr_name = object_stack[-1]["attributes"][-1]["name"]

    small_type_name = snake_to_camel(object_stack[-1]["attributes"][-1]["name"])
    small_type_name = small_type_name[0].upper() + small_type_name[1:]

    return {
        "name": small_type_name,
        "origin": object_stack[-1]["name"],
        "attr_name": attr_name,
        "attributes": _extract_attributes(small_type, attr_name),
        "docstring": f"Small type for attribute '{attr_name}'",
        "type": "object",
        "parent": None,
    }


def _extract_attributes(dtypes: str, attr_name: str) -> List[Dict]:
    """Extracts all attributes from a small type"""

    attributes = []
    for attribute in dtypes.split(","):
        if ":" not in attribute:
            raise ValueError(
                f"Small type: Attribute '{attribute}' for '{attr_name}' is not valid."
            )

        name, dtype = attribute.split(":")
        dtype = re.sub(r"\s+|\}", "", dtype)
        name = re.sub(r"\s+|\{", "", name)

        # Perform checks on the attribute
        _validate_attribute(attribute, attr_name, name, dtype)

        attributes.append(
            {
                "name": name.strip(),
                "type": [dtype.strip("}")],
                "required": False,
            }
        )

    return attributes


def _validate_attribute(attribute, attr_name, name, dtype):
    """Basics checks for an attribute"""

    assert (
        name.strip()
    ), f"Small type: Sub-attribute '{attribute}' for attribute '{attr_name}' has no name."
    assert (
        dtype.strip()
    ), f"Small type: Sub-attribute '{attribute}' for attribute '{attr_name}' has no type."

    if dtype.strip() not in DataTypes.__members__:
        raise ValueError(
            f"Small type: Type '{dtype}' is not valid. Please, only use base datatypes for small types"
        )
