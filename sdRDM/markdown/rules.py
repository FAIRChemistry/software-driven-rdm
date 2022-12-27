from enum import Enum

HEADING_PATTERN = r"##\s"
MODULE_PATTERN = r"#\s"
ENUM_PATTERN = {
    "level": r"####\s",
    "format": r"```(python)?",
    "mapping": r"([A-Za-z0-9\_]*\s?\=\s)",
}
OBJECT_PATTERN = {"level": r"###\s", "inherit": r"\[\_([A-Za-z0-9\_]*)\_\]"}
OPTION_PATTERN = {
    "list": r"\s\s\-\s",
    "description": r"OPTION [D|d]escription:\s?",
    "type": r"OPTION [T|t]ype:\s?",
    "multiple": r"OPTION [M|m]ultiple:\s?",
}
ATTRIBUTE_PATTERN = {
    "list": r"\-\s",
    "bold": r"__",
    "required": r"\*",
    "linked": r"\[([A-Za-z0-9\s\,]*)\]\([\#A-Za-z0-9\s\,]*\)",
}

REPLACEMENTS = [
    (ENUM_PATTERN["level"], "ENUM "),
    (OBJECT_PATTERN["level"], "OBJECT "),
    (HEADING_PATTERN, "HEADING"),
    (MODULE_PATTERN, "MODULE "),
    (OPTION_PATTERN["list"], "OPTION "),
    (ATTRIBUTE_PATTERN["list"], "ATTRIBUTE "),
    (ATTRIBUTE_PATTERN["bold"], ""),
    (OPTION_PATTERN["type"], "TYPE "),
    (OPTION_PATTERN["description"], "ATTRDESCRIPTION "),
    (OPTION_PATTERN["multiple"], "MULTIPLE "),
    (ATTRIBUTE_PATTERN["linked"], r"\1"),
    (OBJECT_PATTERN["inherit"], r"\nPARENT \1"),
    (ENUM_PATTERN["format"], ""),
    (ENUM_PATTERN["mapping"], r"MAPPING \1"),
    (ATTRIBUTE_PATTERN["required"], "\nREQUIRED"),
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
