import importlib
import re
import validators
import os

from typing import Dict, List, Optional, Union

from sdRDM.linking.utils import build_guide_tree
from anytree import findall


def convert_data_model(obj, option: str, template: Dict = {}):
    """
    Converts a given data model to another model that has been specified
    in the attributes metadata. This will create a new object model from
    the current.

    Example:
        ## Origin
        class DataModel(sdRDM.DataModel):
            foo: str = Field(... another_model="AnotherModel.sub.bar")

        --> The goal is to project the data from 'DataModel' to 'AnotherModel'
            which maps the 'foo' attribute to the nested 'bar' attribute.

    This function provides the utility to map in between data models and
    offer an exchange of data without explicit code.

    Args:
        option (str): Key of the attribute metadata, where the destination is stored.
    """

    # Create target roots and map data
    libs = {}
    roots = {
        **_extract_roots_from_template(template=template, libs=libs),
        **_extract_roots(obj=obj, option=option, libs=libs),
    }

    # Transfer data towards the target roots
    _convert_tree(obj=obj, option=option, roots=roots, template=template)

    return [(root.build(), libs[root.name]) for root in roots.values()]


def _extract_roots(obj, option: str, libs: Dict, roots: Dict = {}, template: Dict = {}):
    """
    Parses metadata of all attributes present in this data model and
    extracts the libraries needed for executing the given option.

    This function builds the trees to which the data will be mapped
    later on.

    Args:
        obj (DataModel): Query objet from which everythin will be mapped.
        option (str): Export option that holds target destination.
        roots (dict): Target tree(s) to map to.
    """

    for field in obj.__fields__.values():
        field_options = field.field_info.extra

        if option in field_options:
            lib, root, *_ = field_options[option].split(".")
            lib = importlib.import_module(lib)
            libs[root] = lib
            roots[root] = build_guide_tree(getattr(lib, root))

        if hasattr(field, "__fields__"):
            _extract_roots(obj=field, roots=roots, option=option, libs=libs)
        elif hasattr(field.type_, "__fields__"):
            _extract_roots(obj=field.type_, roots=roots, option=option, libs=libs)

    return roots


def _extract_roots_from_template(template: Dict, libs: Dict) -> Dict:
    """
    Parses the provided linking template and extracts
    the libraries needed for executing the given option.

    This function builds the trees to which the data will be mapped
    later on.

    Args:
        template (Dict): Dictionary containing all infos about links.
        roots (dict): Target tree(s) to map to.
    """

    from sdRDM.base.datamodel import DataModel

    roots = {}

    if template == {}:
        return {}

    if "__constants__" in template:
        constants = template["__constants__"]
    else:
        constants = {}

    # Get sources defined in the templates
    for name, address in template["__sources__"].items():

        if validators.url(address):
            if "@" in address:
                # Get specific tags
                address, tag = address.split("@")
            else:
                # If not given, lets leave this at None
                tag = None

            lib = DataModel.from_git(url=address, tag=tag)
            libs[name] = lib

        elif os.path.exists(address):
            lib = DataModel.from_markdown(address)
            libs[name] = lib
        else:
            lib = importlib.import_module(address)
            libs[name] = lib

        if name in constants:
            local_const = constants[name]
        else:
            local_const = {}

        roots[name] = build_guide_tree(getattr(lib, name), constants=local_const)

    return roots


def _convert_tree(obj, roots, option, template, obj_index=0, attr_path="", target={}):
    """
    Maps values found in a tree to the corresponding target nodes of the
    other data model's tree.

    This function takes the given targets and adds the respective values
    to the nodes of the other data model. If objects of cardinality > 1
    are encountered, these will be stored as indexed dictionaries. This
    way, nested models can be perserved, while the tree can be kept as a
    single instance.


    Args:
        obj (sdRDM.DataModel): Object from which the data will be transfered.
        roots (Dict): Target trees to which the data will be transfered.
        option (str): Export option that holds target destination.
        obj_index (int, optional): Index that is used for 'multiple' objects. Defaults to 0.
    """

    object_name = obj.__class__.__name__
    for attribute, field in obj.__fields__.items():
        field_options = field.field_info.extra
        value = getattr(obj, attribute)

        if value is None:
            continue

        if not isinstance(value, list) and hasattr(field.type_, "__fields__"):
            matches = _check_matching_target(
                obj=value,
                path=f"{attr_path}.{attribute}".strip("."),
                template=template,
            )

            if isinstance(matches, dict):
                # TODO Refactor this
                _convert_tree(
                    obj=value,
                    roots=roots,
                    option=option,
                    obj_index=obj_index,
                    template=template,
                    attr_path=f"{attr_path}.{attribute}".strip("."),
                    target=matches,
                )
            else:
                for match in matches:
                    _convert_tree(
                        obj=value,
                        roots=roots,
                        option=option,
                        obj_index=obj_index,
                        template=template,
                        attr_path=f"{attr_path}.{attribute}".strip("."),
                        target=match["targets"],
                    )

        elif isinstance(value, list) and _only_classes(value):
            wrap_type = _get_wrapping_type(field)
            if wrap_type == "list":
                for i, sub_obj in enumerate(value):

                    matches = _check_matching_target(
                        obj=value[i],
                        path=f"{attr_path}.{attribute}".strip("."),
                        template=template,
                    )

                    if isinstance(matches, dict):
                        # TODO Refactor this
                        _convert_tree(
                            obj=sub_obj,
                            roots=roots,
                            option=option,
                            obj_index=obj_index + i,
                            template=template,
                            attr_path=f"{attr_path}.{attribute}".strip("."),
                            target=matches,
                        )
                    else:
                        for match in matches:
                            _convert_tree(
                                obj=sub_obj,
                                roots=roots,
                                option=option,
                                obj_index=obj_index + i,
                                template=template,
                                attr_path=f"{attr_path}.{attribute}".strip("."),
                                target=match["targets"],
                            )

        else:
            if attribute in target:
                root, *path = target[attribute].split(".")
                node = roots[root]
                _assign_primitive_data_to_node(path, node, value, index=obj_index)

            elif option in field_options:
                _, root, *path = field_options[option].split(".")
                nu_index = f"{attr_path}.{obj_index}"
                node = roots[root]
                _assign_primitive_data_to_node(path, node, value, index=nu_index)

            elif object_name in template and attribute in template[object_name]:
                root, *path = template[object_name][attribute].split(".")
                node = roots[root]
                _assign_primitive_data_to_node(path, node, value, index=obj_index)


def _check_matching_target(obj, path, template):
    """Checks whether one of the targets defined in a template apply and returns it."""
    targets = template.get(path)

    if targets is None:
        return {}
    elif isinstance(targets, dict) and not any(
        [isinstance(options, dict) for options in targets.values()]
    ):
        # Return empty target if the source template is not specified with
        # a filter/regex pattern
        return targets

    matches = []

    for target in targets:
        match_attr = getattr(obj, target["attribute"])
        pattern = target["pattern"]

        if bool(re.match(pattern, str(match_attr))):
            matches.append(target)

    return matches

    if len(matches) > 1:
        raise ValueError(
            f"Object '{obj.__class__.__name__}' at '{path}' matches for {len(matches)} targets. \
            There can only be one match though. Please make sure that when linking, that patterns \
            only apply once.".replace(
                "  ", ""
            )
        )
    elif len(matches) == 0:
        return {}

    return matches[0]["targets"]


def _only_classes(value: List):
    """Checks whether the content of a list are classes"""
    return all(hasattr(obj, "__fields__") for obj in value)


def _assign_primitive_data_to_node(path, node, value, index: Union[str, int] = 0):
    """Adds data to a single nodes dictionary"""
    node = findall(node, _search_by_path(path))[0]
    node.value[index] = value


def _search_by_path(path):
    """Searches a tree for a given node by a given path"""
    return lambda node: [n.name for n in node.path if n.name[0].islower()] == path


def _get_wrapping_type(field):
    """Extracts the outer type of an attribute (e.g. 'List')"""
    origin_type = field.outer_type_.__dict__.get("__origin__")
    if hasattr(origin_type, "__name__"):
        return origin_type.__name__
