import re

from typing import Optional, IO
from markdown_it import MarkdownIt

from sdRDM.validator import validate_markdown_model, pretty_print_report

from .tokens import MarkdownTokens
from .tokenizer import tokenize_markdown_model, clean_html_markdown
from .utils import process_type


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
        html = MarkdownIt().render(handle.read())
        model_string = clean_html_markdown(html)
        tokenized = tokenize_markdown_model(model_string)

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
                    "docstring": None,
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
                    "multiple": False,
                    "default": None,
                    "description": "Not description given.",
                    "type": [],
                }
            )

        elif token == MarkdownTokens.TYPE.value and content:

            dtype, is_composite, exts = process_type(content)

            self.stack[-1]["attributes"][-1]["type"].append(dtype)
            self.external_objects.update(exts)

            if is_composite:
                self.compositions += [
                    {"container": self.stack[-1]["name"], "module": dtype}
                ]

        elif token == MarkdownTokens.ATTRDESCRIPTION.value and content:
            self.stack[-1]["attributes"][-1]["description"] = content

        elif token == MarkdownTokens.REQUIRED.value:
            self.stack[-1]["attributes"][-1]["required"] = True

            if self.stack[-1]["attributes"][-1]["default"] is None:
                del self.stack[-1]["attributes"][-1]["default"]

        elif token == MarkdownTokens.MULTIPLE.value:
            self.stack[-1]["attributes"][-1]["multiple"] = True

            if "default" in self.stack[-1]["attributes"][-1]:
                del self.stack[-1]["attributes"][-1]["default"]

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
            
        elif token == MarkdownTokens.REFERENCE.value and content:
            self.stack[-1]["attributes"][-1]["reference"] = content

    def add_model(self, parser: "MarkdownParser"):
        """Adds another parser to the current one"""

        assert isinstance(
            parser, self.__class__
        ), "Got wrong parser of type {parser.__class__.__name__}"

        self.objs += parser.objs
        self.enums += parser.enums
        self.inherits += parser.inherits
        self.compositions += parser.compositions
        self.external_objects.update(parser.external_objects)
