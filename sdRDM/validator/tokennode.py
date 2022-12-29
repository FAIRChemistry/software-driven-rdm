from copy import deepcopy
from typing import Dict
from anytree import Node

AVAILABLE_TOKENS = [
    'MODULE',
    'OBJECT',
    'DESCRIPTION',
    'ATTRIBUTE',
    'OPTION',
    'TYPE',
    'ATTRDESCRIPTION',
    'REQUIRED',
    'MULTIPLE',
    'PARENT',
    'ENUM',
    'MAPPING',
    'ENDOFMODEL'
]

RULE_NAMES = [
    "occurs_in",
    "mandatory",
    "exclusive",
    "forbidden",
    "pattern"
]

class TokenNode(Node):
    
    def __init__(
        self,
        name,
        parent=None,
        children=None,
        order=0,
        exclusive=False,
        pattern=None,
        occurs_in=None,
        mandatory=None,
        optional=None,
        forbidden=None,
    ):
        super().__init__(name, parent, children)
        self.order = order
        self.occurs_in = occurs_in,
        self.mandatory = mandatory,
        self.exclusive = exclusive,
        self.optional = optional,
        self.forbidden = forbidden,
        self.pattern = pattern
        
        # Get values from all tuples -> Strangely done by '**options'
        for key, value in self.__dict__.items():
            if isinstance(value, tuple):
                setattr(self, key, value[0])
        
    def has_rules(self) -> bool:
        """Whether this node has any rules attached"""
        return any(attr in RULE_NAMES for attr in self.__dict__.keys())

def build_token_tree(rules: Dict) -> Dict[str, TokenNode]:
    """Builds a tree of rules to perform validation"""
    
    nodes = {
        token: TokenNode(token, order=options.pop("order"), **options) 
        for token, options in deepcopy(rules).items()
    }
    
    for parent, options in rules.items():
        if not options.get("mandatory"):
            continue
        
        childs = options["mandatory"]
        
        if "optional" in options:
            childs += options["optional"]
        
        for child in childs:
            
            child = child.strip("!")
            
            try:
                nodes[child].parent = nodes[parent]
            except:
                nodes[child] = TokenNode(name=child, order=child["order"])
                nodes[child].parent = nodes[parent]
                
    return nodes
    