import importlib
from typing import Dict

from sdRDM.linking.utils import build_guide_tree
from anytree import findall


def convert_data_model_by_option(obj, option: str):
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
    roots = _extract_roots(obj=obj, option=option)

    # Transfer data towards the target roots
    _convert_tree(obj=obj, option=option, roots=roots)

    return [root.build() for root in roots.values()]


def _extract_roots(obj, option: str, roots: Dict = {}):
    """
    Parses metadata of all attributes present in this data model and
    extracts the libraries needed for executing the given option.

    This function builds the trees to which the data will be mapped
    later on.

    Args:
        obj (_type_): Query objet from which everythin will be mapped.
        option (str): Export option that holds target destination.
        roots (dict): Target tree(s) to map to.

    Returns:
        _type_: _description_
    """

    for field in obj.__fields__.values():
        field_options = field.field_info.extra

        if option in field_options:
            lib, root, *_ = field_options[option].split(".")
            lib = importlib.import_module(lib)
            roots[root] = build_guide_tree(getattr(lib, root))

        if hasattr(field, "__fields__"):
            _extract_roots(obj=field, roots=roots, option=option)
        elif hasattr(field.type_, "__fields__"):
            _extract_roots(obj=field.type_, roots=roots, option=option)

    return roots


def _convert_tree(obj, roots, option, obj_index=0):
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

    for attribute, field in obj.__fields__.items():
        field_options = field.field_info.extra
        value = getattr(obj, attribute)

        if isinstance(value, list):
            wrap_type = _get_wrapping_type(field)
            if wrap_type == "list":
                for i, sub_obj in enumerate(value):
                    _convert_tree(
                        obj=sub_obj, roots=roots, option=option, obj_index=obj_index + i
                    )

        if option in field_options:
            _, root, *path = field_options[option].split(".")
            node = roots[root]
            _assign_primitive_data_to_node(path, node, value, index=obj_index)


def _assign_primitive_data_to_node(path, node, value, index=0):
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
