from enum import Enum

HEADING_PATTERN = r"<h2>"
MODULE_PATTERN = r"<h1>"
ENUM_PATTERN = {
    "level": r"<h4>",
    "mapping": r"([A-Za-z0-9\_]*\s?\=\s)",
}
OBJECT_PATTERN = {
    "level": r"<h3>",
    "inherit": r"\[<em>([A-Za-z0-9\_]*)</em>\]"
}
OPTION_PATTERN = {
    "list": r"<li>",
    "description": r"OPTION [D|d]escription:\s?",
    "type": r"OPTION [T|t]ype:\s?",
    "reference": r"TYPE \@([A-Za-z0-9\_]*).([A-Za-z0-9\_]*)",
    "multiple": r"OPTION [M|m]ultiple:\s?",
}
ATTRIBUTE_PATTERN = {
    "list": r"<li><strong>",
    "required": r"\*",
    "linked": r'<a href="#[a-z0-9\_]*">([A-Za-z0-9\_]*)</a>',
}

REPLACEMENTS = [
    (ENUM_PATTERN["level"], "ENUM "),
    (OBJECT_PATTERN["level"], "OBJECT "),
    (HEADING_PATTERN, "HEADING "),
    (MODULE_PATTERN, "MODULE "),
    (ATTRIBUTE_PATTERN["list"], "ATTRIBUTE "),
    (OPTION_PATTERN["list"], "OPTION "),
    (OPTION_PATTERN["type"], "TYPE "),
    (OPTION_PATTERN["description"], "ATTRDESCRIPTION "),
    (OPTION_PATTERN["multiple"], "MULTIPLE "),
    (ATTRIBUTE_PATTERN["linked"], r"\1"),
    (OBJECT_PATTERN["inherit"], r"\nPARENT \1"),
    (ENUM_PATTERN["mapping"], r"MAPPING \1"),
    (ATTRIBUTE_PATTERN["required"], "\nREQUIRED"),
    (OPTION_PATTERN["reference"], r"TYPE \1\nREFERENCE \1.\2")
]


class MarkdownTokens(Enum):
    """Tokens used in the context of markdown parsing and validation"""

    ENUM = "ENUM"
    OBJECT = "OBJECT"
    HEADING = "HEADING"
    MODULE = "MODULE"
    OPTION = "OPTION"
    ATTRIBUTE = "ATTRIBUTE"
    TYPE = "TYPE"
    DESCRIPTION = "DESCRIPTION"
    ATTRDESCRIPTION = "ATTRDESCRIPTION"
    PARENT = "PARENT"
    MAPPING = "MAPPING"
    REQUIRED = "REQUIRED"
    MULTIPLE = "MULTIPLE"
    REFERENCE = "REFERENCE"
