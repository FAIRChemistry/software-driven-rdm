from typing import List, Tuple, Dict, IO
from markdown_it import MarkdownIt
from markdown_it.token import Token

from sdRDM.generator.utils import camel_to_snake

from .enumutils import parse_markdown_enumerations
from .objectutils import parse_markdown_module


class MarkdownParser:
    def __init__(self) -> None:
        self.objects = []
        self.enums = []
        self.inherits = []
        self.compositions = []
        self.external_objects = {}

    @classmethod
    def parse(cls, handle: IO):
        """Parses a given markdown file to a mermaid schema from which code is generated."""

        parser = cls()

        doc = MarkdownIt().parse(handle.read())
        modules, enumerations = parser.get_objects_and_enumerations(doc)

        for module, model in modules.items():
            parser.objects += [obj for obj in parse_markdown_module(module, model)]

        parser.enums = parse_markdown_enumerations(enumerations)

        # Parse given structure
        parser.get_compositions()
        parser.get_inherits()

        return parser

    def add_model(self, parser: "MarkdownParser"):
        """Adds another parser to the current one"""

        assert isinstance(
            parser, self.__class__
        ), f"Got wrong parser of type {parser.__class__.__name__}"

        self.objects += parser.objects
        self.enums += parser.enums
        self.inherits += parser.inherits
        self.compositions += parser.compositions
        self.external_objects.update(parser.external_objects)

    def get_objects_and_enumerations(
        self,
        doc: List[Token],
    ) -> Tuple[Dict[str, List[Token]], List[Token]]:
        """Gets all objects and enumerations denoted by H2 headings"""

        objects, enumerations = {}, []
        h2_indices = self.get_h2_indices(doc)
        for index, (module, start) in enumerate(h2_indices[0:-1]):

            end = h2_indices[index + 1][-1]
            model_part = doc[start:end]

            if module.lower() == "enumerations":
                enumerations += model_part
            else:
                objects[camel_to_snake(module)] = model_part

        return objects, enumerations

    def get_h2_indices(self, doc: List[Token]) -> List[Tuple[str, int]]:
        """Returns all H2 indices to extract objects and enumerations"""
        return [
            (doc[index + 1].content, index)
            for index, token in enumerate(doc)
            if token.tag == "h2" and token.type == "heading_open"
        ] + [("END", len(doc))]

    def get_inherits(self) -> None:
        """Gets all inheritance cases present in the data model"""

        for object in self.objects:
            if not "parent" in object:
                continue

            self.inherits.append({"parent": object["parent"], "child": object["name"]})

    def get_compositions(self) -> None:
        """Find all compositions across the model and add them to the parser"""

        for object in self.objects:
            dtypes = self.find_types(
                self.acummulate_dtypes(object), self.enums + self.objects
            )

            self.compositions += [
                {"container": object["name"], "module": dtype} for dtype in dtypes
            ]

    @staticmethod
    def acummulate_dtypes(object: Dict) -> List[str]:
        """Accumulates all types found within the attributes of an object"""

        return [
            dtype for attribute in object["attributes"] for dtype in attribute["type"]
        ]

    @staticmethod
    def find_types(dtypes: List[str], elements: List[Dict]) -> List[str]:
        """Finds types across objects and enums"""

        return [element["name"] for element in elements if element["name"] in dtypes]
