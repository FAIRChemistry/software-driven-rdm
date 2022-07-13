import importlib

from anytree import Node

class ClassNode(Node):
    def __init__(self, name, parent=None, module=None, class_name=None, outer_type=None):
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
        kwargs = {
            node.name: node.value
            for node in self.children
        }
        
        cls = self.import_class()
        
        return cls(**kwargs)
        
class AttributeNode(Node):
    def __init__(self, name, parent=None, value=None, outer_type=None):
        super().__init__(name, parent)
        
        self.value = value
        self.outer_type = outer_type