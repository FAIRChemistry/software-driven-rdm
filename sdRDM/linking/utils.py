import yaml

from anytree import LevelOrderGroupIter

from sdRDM.linking.nodes import AttributeNode, ClassNode
from sdRDM.tools.utils import YAMLDumper

DEFAULT_MAPPINGS = {"list": list, "dict": dict}


def build_guide_tree(obj, parent=None, outer=None):
    """Creates a binary tree representation from the underlying data model.

    Args:
        obj (Callable): Object from which the tree is constructed.
        parent (Node, optional): Parent node to which the node will be added if provided. Defaults to None.
        outer (Any, optional): Data structure into which the actual data type is wrapped. Defaults to None.

    Returns:
        Node: Tree representation of the data model.
    """

    obj_tree = ClassNode(
        obj.__name__,
        parent=parent,
        module=obj.__module__,
        class_name=obj.__name__,
        outer_type=outer,
    )

    for name, field in obj.__fields__.items():
        inner_type = field.type_
        outer_type = field.outer_type_.__dict__.get("__origin__")

        if outer_type and outer_type.__module__ == "builtins":
            value = DEFAULT_MAPPINGS[outer_type.__name__]()
        else:
            value = None

        current_parent = AttributeNode(
            name, parent=obj_tree, outer_type=outer_type, value=value
        )

        if inner_type.__module__ != "builtins" and hasattr(inner_type, "__fields__"):
            build_guide_tree(inner_type, current_parent, outer=outer_type)

    return obj_tree


def generate_template(obj, out: str) -> None:
    """Generates a template for linking two datasets."""

    template = {"__model__": obj.__name__}
    for nodes in LevelOrderGroupIter(obj.create_tree()[0]):
        for node in nodes:
            path = _get_path(node.path)

            if isinstance(node, ClassNode) and path:
                attr_template = {n.name: "Enter target" for n in node.children}
                template[path] = [
                    {
                        "attribute": "ObjectAttribute",
                        "pattern": r"[A-Za-z0-9]",
                        "targets": attr_template,
                    }
                ]

    with open(out, "w") as f:
        f.write(yaml.dump(template, Dumper=YAMLDumper))


def _get_path(path):
    """Parses a tree path to a symbolic path through the data model"""
    return ".".join([node.name for node in path if node.name[0].islower()])
