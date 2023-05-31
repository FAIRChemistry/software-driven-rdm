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
