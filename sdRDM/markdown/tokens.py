from enum import Enum


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
