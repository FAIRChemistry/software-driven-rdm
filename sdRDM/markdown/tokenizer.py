import re

from typing import List, Tuple, Optional, Any
from .tokens import REPLACEMENTS, MarkdownTokens


def tokenize_markdown_model(
    model_string: str,
) -> List[Tuple[Optional[str], Optional[str]]]:
    """Turns headings in tokens to facilitate separation"""

    for target, replacement in REPLACEMENTS:
        model_string = re.sub(target, replacement, model_string)

    # Remove unused lines
    tokenized = filter(str.strip, model_string.split("\n"))

    model = []
    for line in tokenized:
        token, value = tupelize(line.strip())

        if token == MarkdownTokens.TYPE.value:
            model += [(token, dtype) for dtype in value]
        else:
            model += [(token, value)]

    return model + [("ENDOFMODEL", None)]


def tupelize(line: str) -> Tuple[Optional[str], Any]:
    """Takes a raw token and content string and turns it into a tuple"""

    if has_token(line):
        splitted = line.split(" ", 1)
        if len(splitted) == 1:
            return (splitted[0], None)
        else:
            if splitted[0] == MarkdownTokens.TYPE.value:
                # Special case: Handle multiple data types
                return (splitted[0], check_type_token_exception(splitted[-1]))

            return (splitted[0], splitted[1].strip())
    else:
        return ("DESCRIPTION", line)


def check_type_token_exception(type: str) -> List[str]:
    """Due to the option of possible multiple types for an attribute,
    these need to be handled exclusively.
    """
    return [t.strip() for t in type.split(",")]


def has_token(line: str):
    """Checks whether there is a token in the line"""
    return any(line.strip().startswith(token) for token in MarkdownTokens.__members__)
