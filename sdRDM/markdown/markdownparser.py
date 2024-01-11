import re

from typing import List, Tuple, Dict, IO
from markdown_it import MarkdownIt
from markdown_it.token import Token
from pydantic import BaseModel

from sdRDM.generator.utils import camel_to_snake

from .enumutils import parse_markdown_enumerations
from .objectutils import parse_markdown_module


class MarkdownParser(BaseModel):
    objects: List = []
    enums: List = []
    inherits: List = []
    compositions: List = []
    external_objects: Dict = {}

    @classmethod
    def parse(cls, handle: IO):
        """Parses a given markdown file to a mermaid schema from which code is generated."""

        parser = cls()

        doc = MarkdownIt().parse(cls.clean_html_tags(handle.readlines()))
        modules, enumerations = parser.get_objects_and_enumerations(doc)

        for module, model in modules.items():
            parser.objects += [
                obj
                for obj in parse_markdown_module(module, model, parser.external_objects)
            ]

        parser.enums = parse_markdown_enumerations(enumerations)

        # Add external objects to the current parser
        parser.merge_external_objects()

        # Parse given structure
        parser.get_compositions()
        parser.get_inherits()

        return parser

    def add_model(self, parser: "MarkdownParser"):
        """Adds another parser to the current one"""

        assert isinstance(
            parser, self.__class__
        ), f"Expected parser of type 'MarkdownParser' got '{type(parser)}' instead."

        duplicate_objects = self._has_duplicate_object_names(parser)
        assert (
            not duplicate_objects
        ), f"A given remote model has redundant object names: {duplicate_objects}"

        self.objects += parser.objects
        self.enums += parser.enums
        self.inherits += parser.inherits
        self.compositions += parser.compositions
        self.external_objects.update(parser.external_objects)

    def _has_duplicate_object_names(self, parser):
        """Checks whether there are redundancies within the model"""

        assert isinstance(
            parser, self.__class__
        ), f"Expected parser of type 'MarkdownParser' got '{type(parser)}' instead."

        self_names = set([obj["name"] for obj in self.objects])
        parser_names = set([obj["name"] for obj in parser.objects])

        return self_names.intersection(parser_names)

    def merge_external_objects(self):
        """Merges all remote objects into the current parser"""

        for external_def in self.external_objects.values():
            self.add_model(external_def)

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

            # Avoid duplication of inheritance cases
            if object["name"] in [inherit["child"] for inherit in self.inherits]:
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

    @staticmethod
    def clean_html_tags(model: List[str]):
        """Removes all lines that contain html tags that are used for styling
        the markdown file"""

        HTML_TAG_PATTERN = re.compile(r"<.*?>")

        return "".join([line for line in model if not HTML_TAG_PATTERN.search(line)])
