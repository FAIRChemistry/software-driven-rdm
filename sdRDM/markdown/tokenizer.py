import re

from typing import List, Tuple, Optional
from .rules import REPLACEMENTS, MarkdownTokens

def tokenize_markdown_model(model_string: str) -> List[Tuple[Optional[str], Optional[str]]]:
    """Turns headings in tokens to facilitate separation"""

    for target, replacement in REPLACEMENTS:
        model_string = re.sub(target, replacement, model_string)
            
    # Remove unused lines
    tokenized = filter(
        str.strip,
        model_string.split("\n")
    )
            
    return list(map(tupelize, tokenized)) + [("ENDOFMODEL", None)]
    
def tupelize(line: str) -> Tuple[Optional[str], Optional[str]]:
    """Takes a raw token and content string and turns it into a tuple"""
    
    if has_token(line):
        splitted = line.split(" ", 1)
        if len(splitted) == 1:
            return (splitted[0], None)
        else:
            return (splitted[0], splitted[1])
    else:
        return ("DESCRIPTION", line)
    
def has_token(line: str):
    """Checks whether there is a token in the line"""
    return any(line.startswith(token) for token in MarkdownTokens.__members__)