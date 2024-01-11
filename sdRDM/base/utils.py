import re

from typing import Dict, List, Optional
from inspect import Signature, Parameter
from pydantic import Field, create_model

from sdRDM.base.importedmodules import ImportedModules


def generate_model(
    data: Dict,
    name: str,
    base,
    attr_replace: str,
    objs: Dict = {},
    is_root: bool = True,
):
    """Generates a model based on a given file without an existing schema.

    Caution, these models can impose to be incomplete if the data given
    only covers a fraction of the actual schema it was generated from.
    This methods intent is to provide sdRDM's functionalities for parsing
    data on the fly.

    """

    fields = {}
    for field, content in data.items():
        field_params = {}
        if (
            isinstance(content, list)
            and content != []
            and all(isinstance(entry, dict) for entry in content)
        ):
            field_params["default_factory"] = list
            dtype = List[
                generate_model(
                    data=content[0],
                    name=field.capitalize(),
                    base=base,
                    objs=objs,
                    is_root=False,
                    attr_replace=attr_replace,
                )  # type: ignore
            ]
        elif isinstance(content, dict):
            dtype = generate_model(
                data=content,
                name=field.capitalize(),
                base=base,
                objs=objs,
                is_root=False,
                attr_replace=attr_replace,
            )  # type: ignore
        elif isinstance(content, list):
            field_params["default_factory"] = list
            dtype = List[type(content[0])]
        else:
            field_params["default"] = None
            dtype = Optional[type(content)]

        # Perform attribute replacement
        new_name = re.sub(attr_replace, "", field)
        new_name = new_name.replace("-", "_")

        if new_name != field:
            field_params["alias"] = field
            field = new_name

        fields[field] = (dtype, Field(**field_params))

    # Finally create the corresponding object
    objs[name] = create_model(name, __base__=base, **fields)

    if is_root:
        return ImportedModules(classes=objs)
    else:
        return objs[name]


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
        if f"{name}_" in cls.model_fields:
            name = f"{name}_"

        parameters.append(
            Parameter(
                name=name,
                kind=parameter.kind,
                default=parameter.default,
                annotation=parameter.annotation,
            )
        )

    return parameters
