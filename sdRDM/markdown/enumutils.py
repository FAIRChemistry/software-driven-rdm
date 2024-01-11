import re

from markdown_it.token import Token
from typing import List, Dict


MAPPING_PATTERN = r"([A-Za-z0-9\_]*)\s*\=\s*(.*)"


def parse_markdown_enumerations(enumerations: List[Token]) -> List[Dict]:
    """Parses enumerations defined in a markdown model"""

    enum_stack = []
    for index, element in enumerate(enumerations):
        if element.level == 1 and enumerations[index - 1].tag == "h3":
            enum_stack.append(
                {
                    "name": element.content,
                    "docstring": "",
                    "mappings": [],
                    "type": "enum",
                }
            )

        elif element.level == 1 and enumerations[index - 1].tag == "p":
            enum_stack[-1]["docstring"] += element.content

        elif element.level == 0 and element.content.strip():
            mappings = element.content.strip().split("\n")

            for mapping in mappings:
                match = re.match(MAPPING_PATTERN, mapping)

                assert bool(
                    re.match(MAPPING_PATTERN, mapping)
                ), f"Mapping '{mapping}' does not follow the synatx rules."

                assert match is not None, f"No groups found for mapping '{mapping}'"

                key, value = match.group(1, 2)

                enum_stack[-1]["mappings"].append({"key": key, "value": value})

    return enum_stack
