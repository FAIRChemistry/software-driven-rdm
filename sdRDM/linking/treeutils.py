from .nodes import AttributeNode, ClassNode


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

        current_parent = AttributeNode(name, parent=obj_tree, outer_type=outer_type)

        if inner_type.__module__ != "builtins" and hasattr(inner_type, "__fields__"):
            build_guide_tree(inner_type, current_parent, outer=outer_type)

    return obj_tree
