import yaml
import toml

from anytree import LevelOrderIter
from pydantic.main import ModelMetaclass
from typing import get_origin

from sdRDM.linking.nodes import AttributeNode, ClassNode, ListNode
from sdRDM.tools.utils import YAMLDumper


def build_guide_tree(obj: "DataModel") -> ClassNode:
    """Builds a tree of AttributeNodes and ClassNodes from a data model.

    Args:
        obj (DataModel): Object to build the tree from

    Returns:
        ClassNode: Tree of AttributeNodes and ClassNodes representing the data model
    """

    if isinstance(obj, ModelMetaclass):
        return _build_class_tree(obj)

    return _build_instance_tree(obj)


def _build_class_tree(obj: "DataModel", parent=None):
    """Builds a tree of AttributeNodes and ClassNodes from an uninstantiated data model."""

    if parent is None:
        parent = ClassNode(obj.__name__, parent=parent)

    for name, field in obj.__fields__.items():
        attr_node = AttributeNode(name, parent=parent)

        if _is_multiple_type(field.outer_type_, field.type_):
            attr_node = ListNode("0", parent=attr_node)

        if hasattr(field.type_, "__fields__"):
            _build_class_tree(field.type_, parent=attr_node)

    return parent


def _is_multiple_type(outer_type, type) -> bool:
    """Checcks whether the given outer type is an iterable"""
    return get_origin(outer_type) == list and hasattr(type, "__fields__")


def _build_instance_tree(obj: "DataModel", parent=None) -> ClassNode:
    """Builds a tree of AttributeNodes and ClassNodes from an instantiated data model."""

    cls_node = ClassNode(obj.__class__.__name__, parent=parent)

    for key, value in obj:
        attr_node = AttributeNode(key)
        attr_node.parent = cls_node

        if isinstance(value, list) and all(_is_data_model(item) for item in value):
            for index, item in enumerate(value):
                list_node = ListNode(str(index))
                list_node.parent = attr_node
                _build_instance_tree(item, parent=list_node)
        elif _is_data_model(value):
            _build_instance_tree(value, parent=attr_node)
        else:
            attr_node.value = value

    return cls_node


def _is_data_model(obj):
    """Checks if an object is a data model."""
    return hasattr(obj, "__fields__")


def generate_template(obj, out: str, simple: bool = True) -> None:
    """Generates a template for linking two datasets."""

    template = {
        "__model__": obj.__name__,
        "__sources__": {
            "LibName": "URL to the library",
        },
    }

    # Add attributes of root objects
    template[obj.__name__] = {
        n.name: "Enter target"
        for n in obj.create_tree()[0].children
        if isinstance(n, AttributeNode) and len(n.children) == 0
    }

    for node in LevelOrderIter(obj.create_tree()):
        path = _get_path(node.node_path)

        if node.children and path:
            attr_template = {
                n.name: "Enter target" for n in node.children if len(n.children) == 0
            }

            if simple:
                template[path] = attr_template
            else:
                template[path] = [
                    {
                        "attribute": "Name of the target to check for",
                        "pattern": r".*",
                        "targets": attr_template,
                    }
                ]

    with open(out, "w") as f:
        if not simple:
            f.write(yaml.dump(template, Dumper=YAMLDumper, sort_keys=False))
            return

        f.write(toml.dumps(template))


def _get_path(path):
    """Parses a tree path to a symbolic path through the data model"""
    return ".".join([node.name for node in path if node.name[0].islower()])
