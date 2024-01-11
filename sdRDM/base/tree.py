import re
from typing import get_args, get_origin
from bigtree import Node


class AttributeNode(Node):
    def __init__(self, name, parent=None, value=None, outer_type=None, id=None):
        super().__init__(name=name, parent=parent)

        self.value = value
        self.outer_type = outer_type
        self.id = id


class ListNode(Node):
    pass


class ClassNode(Node):
    def __init__(
        self,
        name,
        parent=None,
        id=None,
        module=None,
        class_name=None,
        outer_type=None,
        constants={},
    ):
        super().__init__(name=name, parent=parent)

        self.module = module
        self.class_name = class_name
        self.outer_type = outer_type
        self.constants = constants
        self.id = id


def build_guide_tree(obj: "DataModel") -> ClassNode:
    """Builds a tree of AttributeNodes and ClassNodes from a data model.

    Args:
        obj (DataModel): Object to build the tree from

    Returns:
        ClassNode: Tree of AttributeNodes and ClassNodes representing the data model
    """

    from sdRDM.base.datamodel import DataModel

    if isinstance(obj, DataModel):
        return _build_instance_tree(obj)

    return _build_class_tree(obj)


def _build_class_tree(obj: "DataModel", parent=None):
    """Builds a tree of AttributeNodes and ClassNodes from an uninstantiated data model."""

    if parent is None:
        parent = ClassNode(obj.__name__, parent=parent)

    for name, field in obj.model_fields.items():
        if _is_recursive(obj, field.annotation):
            AttributeNode(
                f"{name} (Recursive - {field.annotation.__name__})", parent=parent
            )
            continue

        attr_node = AttributeNode(name, parent=parent)
        is_multiple = get_origin(field.annotation) == list
        is_object = any(_is_data_model(item) for item in get_args(field.annotation))
        extra = field.json_schema_extra

        if extra and extra.get("reference"):
            continue

        if not is_object:
            continue

        if is_multiple:
            attr_node = ListNode("0", parent=attr_node)

        dtype = [
            dtype for dtype in get_args(field.annotation) if _is_data_model(dtype)
        ][0]
        _build_class_tree(dtype, parent=attr_node)

    return parent


def _is_recursive(obj: "DataModel", type) -> bool:
    """Checks whether the given type is recursive"""
    return hasattr(type, "model_fields") and obj.model_fields == type.model_fields


def _is_multiple_type(dtype) -> bool:
    """Checcks whether the given outer type is an iterable"""

    is_mulitple = get_origin(dtype) == list
    is_data_model = any(_is_data_model(item) for item in get_args(dtype))

    return is_mulitple and is_data_model


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
    return hasattr(obj, "model_fields")


def _digit_free_path(path: str):
    """Clears all digits from a path"""
    return re.sub(r"\/\d+\/", "/", path)
