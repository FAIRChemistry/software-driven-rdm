import re

from typing import Optional, IO

from sdRDM.validator import validate_markdown_model, pretty_print_report

from .tokens import MarkdownTokens
from .tokenizer import tokenize_markdown_model
from .utils import process_types


class MarkdownParser:
    def __init__(self) -> None:
        self.objs = []
        self.enums = []
        self.inherits = []
        self.compositions = []
        self.external_objects = {}
        self.module_name = "NoName"
        self.module_docstring = []
        self.stack = []

    @classmethod
    def parse(cls, handle: IO):
        """Parses a given markdown file to a mermaid schema from which code is generated.

        Args:
            path (str): Path to the markdown file.
        """

        parser = cls()

        # Read, discard empty lines and tokenize
        lines = "".join([line for line in handle.readlines() if line != "\n"])
        tokenized = tokenize_markdown_model(lines)

        # Validate model
        handle.seek(0)
        is_valid, report = validate_markdown_model(handle=handle)

        if not is_valid:
            pretty_print_report(report, tokenized)
            raise ValueError(
                f"Given Markdown model is not valid. Please see the report above."
            )
            

        for token, content in tokenized:
            # Process tokens one by one
            parser.process_token_line(token=token, content=content)

        # Extract objects and enums
        parser.enums = list(filter(lambda e: e["type"] == "enum", parser.stack))
        parser.objs = list(filter(lambda e: e["type"] == "object", parser.stack))

        del parser.stack

        return parser

    def process_token_line(self, token: Optional[str], content: Optional[str]) -> None:
        """Process a token and content pair that will be sorted accordingly"""

        # OBJECT Handling
        if token == MarkdownTokens.OBJECT.value and content:
            self.stack.append(
                {
                    "name": content,
                    "type": "object",
                    "docstring": "",
                    "attributes": [],
                    "mappings": [],
                }
            )

        elif token == MarkdownTokens.PARENT.value:
            self.inherits.append({"parent": content, "child": self.stack[-1]["name"]})

        # ATTRIBUTE Handling
        elif token == MarkdownTokens.ATTRIBUTE.value and content:
            self.stack[-1]["attributes"].append(
                {
                    "name": content,
                    "required": False,
                    "description": "Not description given.",
                }
            )

        elif token == MarkdownTokens.TYPE.value and content:
            dtype, comps, exts = process_types(content)

            self.stack[-1]["attributes"][-1]["type"] = dtype
            self.external_objects.update(exts)
            self.compositions += [
                {"container": self.stack[-1]["name"], "module": comp}
                for comp in comps
                if comp is not None
            ]

        elif token == MarkdownTokens.ATTRDESCRIPTION.value and content:
            self.stack[-1]["attributes"][-1]["description"] = content

        elif token == MarkdownTokens.REQUIRED.value:
            self.stack[-1]["attributes"][-1]["required"] = True

        elif token == MarkdownTokens.MULTIPLE.value:
            self.stack[-1]["attributes"][-1]["required"] = True

        elif token == MarkdownTokens.OPTION.value and content:
            key, value = re.split(r"\s?\:\s?", content)
            self.stack[-1]["attributes"][-1][key.lower()] = value

        # ENUM Handling
        elif token == MarkdownTokens.ENUM.value:
            self.stack.append(
                {
                    "name": content,
                    "type": "enum",
                    "docstring": "",
                    "attributes": [],
                    "mappings": [],
                }
            )

        elif token == MarkdownTokens.MAPPING.value and content:
            key, value = re.split(r"\s?\=\s?", content)
            self.stack[-1]["mappings"].append({"key": key, "value": value})
