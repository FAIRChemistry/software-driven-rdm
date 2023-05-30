import importlib
import copy

from anytree import LevelOrderGroupIter

from bigtree import Node

# from anytree import Node
from typing import Any, List, get_origin


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

    def import_class(self):
        """Imports the class that is described in this node"""

        assert self.module, "Module is empty"
        assert self.class_name, "No class name given"

        module = importlib.import_module(self.module)
        return getattr(module, self.class_name)

    def instantiate(self):
        """Instantiates the class connected to this node"""

        cls = self.import_class()

        kwargs = self._get_kwargs()
        return cls(**kwargs)

    @staticmethod
    def _is_empty(value):
        if value == {}:
            return True
        elif any([bool(entry) for entry in list(value.values())]):
            return False
        elif not all([bool(entry) for entry in list(value.values())]):
            return True

        return False

    def _get_kwargs(self):
        """Generates list of keyword arguments used to set up a sub class"""

        # Get all constants from the template
        path = (
            ".".join([node.name for node in self.node_path if node.name[0].islower()])
            + "."
        )

        if path == ".":
            path = ""

        attributes = [f"{path}{node.name}" for node in self.children]
        constants = {
            target.split(".")[-1]: value
            for target, value in self.constants.items()
            if target in attributes
        }

        kwargs = {}

        for child in self.children:
            kwargs[child.name] = child.value

        return {**kwargs, **constants}

    def _get_unique_indices(self):
        """Gets all keys in a nodes value dictionary"""
        return {index for node in self.children for index in node.value.keys()}

    def build(self):
        """Instantiates all children that are present in this (sub-)tree and builds the data model.

        (1) Build a list of all levels present
        (2) Reverse the list and work from leaves to root
        (3) Instantiate each sub-class and add it to the parent root
        (4) Stop when the current node is reached

        Returns:
            sdRDM.DataModel: Instantiated tree of the data model
        """

        # self_copy = copy.deepcopy(self)
        level_order = list(LevelOrderGroupIter(self))[::-1]

        for level in level_order:
            if all(isinstance(node, AttributeNode) for node in level):
                print("ATTRS", level)
                continue
            else:
                print("CLLAS", level)

            for node in level:
                if node == self:
                    # Stop the flow once the root node is reached
                    continue

                # Instantiate and get the parent
                cls = node.instantiate()
                parent = node.parent

                parent.value = cls

        return self.instantiate()
