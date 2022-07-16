import importlib
import copy

from anytree import Node, LevelOrderGroupIter


class ClassNode(Node):
    def __init__(
        self, name, parent=None, module=None, class_name=None, outer_type=None
    ):
        super().__init__(name, parent)

        self.module = module
        self.class_name = class_name
        self.outer_type = outer_type

    def import_class(self):
        """Imports the class that is described in this node"""
        module = importlib.import_module(self.module)
        return getattr(module, self.class_name)

    def instantiate(self):
        """Instantiates the class connected to this node"""

        # Parse child nodes
        kwargs = {node.name: node.value for node in self.children}

        cls = self.import_class()

        return cls(**kwargs)

    def build(self):
        """Instantiates all children that are present in this (sub-)tree and builds the data model.

        (1) Build a list of all levels present
        (2) Reverse the list and work from leaves to root
        (3) Instantiate each sub-class and add it to the parent root
        (4) Stop when the current node is reached

        Returns:
            sdRDM.DataModel: Instantiated tree of the data model
        """

        self_copy = copy.deepcopy(self)
        level_order = list(LevelOrderGroupIter(self_copy))[::-1]

        for level in level_order:
            if all(isinstance(node, AttributeNode) for node in level):
                continue

            for node in level:
                if node == self_copy:
                    # Stop the flow once the root node is reached
                    continue

                # Instantiate and get the parent
                cls = node.instantiate()
                parent = node.parent

                if parent.outer_type.__name__ == "list":
                    # Check for list processing
                    if cls.dict(exclude_none=True):
                        parent.value.append(cls)
                else:
                    # If not outer type, assign it
                    parent.value = cls

        return self_copy.instantiate()


class AttributeNode(Node):
    def __init__(self, name, parent=None, value=None, outer_type=None):
        super().__init__(name, parent)

        self.value = {}
        self.outer_type = outer_type
