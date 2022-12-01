import re

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List

from sdRDM.generator.datatypes import DataTypes
from sdRDM.generator.abstractparser import SchemaParser

MODULE_PATTERN = r"^#{1}\s"
OBJECT_PATTERN = r"^#{3}\s"
ENUM_PATTERN = r"^#{4}\s"
ENUM_VALUE_PATTERN = r"[A-Z0-9a-z]*\s?\=\s?.*"
ATTRIBUTE_PATTERN = r"- __([A-Za-z0-9\_]*)(\*?)__"
OPTION_PATTERN = r"([A-Za-z\_]*)\s?\:\s(.*)?"
SUPER_PATTERN = r"\[\_([A-Za-z0-9]*)\_\]"
OBJECT_NAME_PATTERN = r"^\#{2,3}\s*([A-Za-z]*)\s*"
LINKED_TYPE_PATTERN = r"\[([A-Za-z0-9\s\,]*)\]\([\#A-Za-z0-9\s\,]*\)"
GITHUB_TYPE_PATTERN = r"(http[s]?://[www.]?github.com/[A-Za-z0-9\/\-\.\_]*[.git]?)"

MANDATORY_OPTIONS = ["description", "type"]
FORBIDDEN_NAMES = ["yield", "list", "dict", "return", "def", "class"]


class State(Enum):

    NEW_MODULE = auto()
    INSIDE_MODULE = auto()

    NEW_OBJECT = auto()
    INSIDE_OBJECT = auto()
    INSIDE_ATTRIBUTE = auto()
    NEW_ATTRIBUTE = auto()

    NEW_ENUM = auto()
    INSIDE_ENUM = auto()
    NEW_ENUM_VALUE = auto()

    END_OF_FILE = auto()
    IDLE = auto()


@dataclass
class MarkdownParser(SchemaParser):

    module_name: str = ""
    state: State = State.IDLE
    attr: Dict = field(default_factory=dict)
    obj: Dict = field(default_factory=dict)
    objs: List = field(default_factory=list)
    enums: List = field(default_factory=list)
    external_objects: Dict = field(default_factory=dict)
    inherits: List = field(default_factory=list)
    compositions: List = field(default_factory=list)
    module_docstring: List[str] = field(default_factory=list)

    @classmethod
    def parse(cls, handle):

        # Open the markdown file, clean it and set up the parser
        lines = [line for line in handle.readlines() if line != "\n"]
        parser = cls()

        # Perform parsing
        for index, line in enumerate(lines):
            if not line.strip():
                continue

            if bool(re.match(MODULE_PATTERN, line)):
                # Used to start the parsing process
                parser.state = State.NEW_MODULE
            elif parser.state == State.IDLE:
                continue

            if bool(re.match(OBJECT_PATTERN, line)):
                parser.state = State.NEW_OBJECT

            elif bool(re.match(ATTRIBUTE_PATTERN, line)):
                parser.state = State.NEW_ATTRIBUTE

            elif re.findall(OPTION_PATTERN, line):
                parser.state = State.INSIDE_ATTRIBUTE

            elif re.findall(ENUM_PATTERN, line):
                parser.state = State.NEW_ENUM

            elif re.findall(ENUM_VALUE_PATTERN, line):
                parser.state = State.NEW_ENUM_VALUE

            elif (
                not re.findall(ENUM_VALUE_PATTERN, line)
                and parser.state == State.NEW_ENUM_VALUE
            ):
                parser.enums.append(parser.enum)
                parser.state = State.NEW_MODULE

            elif line.startswith("```") and parser.state == State.NEW_ENUM_VALUE:
                parser.state = State.NEW_MODULE

            elif not line.startswith("-") and parser.state == State.INSIDE_ATTRIBUTE:
                parser.state = State.NEW_MODULE

            parser.parse_line(line, index)

            if index == len(lines) - 1:
                # End of the file is reached
                # doctsring will be merged into a single string
                if parser.obj.get("docstring"):
                    parser.obj["docstring"] = "\n".join(parser.obj["docstring"]).strip()
                parser.state = State.END_OF_FILE

        # Concatenate docstring
        parser.module_docstring = "\n".join(parser.module_docstring).strip()  # type: ignore

        return parser

    def parse_line(self, line: str, index: int):

        if self.state is State.NEW_MODULE:
            # Parses name whenever a new module is encountered
            # Sets state to INSIDE_MODULE to catch the docstring

            if not "```" in line.strip():
                self.module_name = line.replace("#", "").strip()
            self.state = State.INSIDE_MODULE

        elif self.state is State.INSIDE_MODULE:
            # Catches the docstring of the module

            if not hasattr(self, "module_docstring"):
                self.module_docstring = [line]
            elif not line.strip().startswith("-"):
                self.module_docstring.append(line)

        elif self.state is State.NEW_OBJECT:
            # New objects will trigger the following workflow
            #
            # (0) Finalize previous objects for intermediate ones
            # (1) Reset object an attributes
            # (2) Gather the object name
            # (3) Set Parser state to INSIDE_OBJECT

            # Add the last attribute and object
            self._check_compositions()
            self._add_attribute_to_obj()
            if self.obj:
                if "docstring" in self.obj:
                    self.obj["docstring"] = "\n".join(self.obj["docstring"])
                self.objs.append(self.obj.copy())

            # Reset object and attributes
            self.obj = {"attributes": []}
            self.attr = {}

            # Parse new object
            self._parse_object_name(line, index)

            # Set state to inside an object
            self.state = State.INSIDE_OBJECT

        elif self.state is State.INSIDE_OBJECT:
            # Catches the docstring of the object

            if line.strip() and self.obj:

                if "docstring" in self.obj:
                    self.obj["docstring"].append(line)
                else:
                    self.obj["docstring"] = [line]

        elif self.state is State.INSIDE_ATTRIBUTE:
            # Parses a line containing attribute options
            # Example: 'Type: string' or 'XML: attribute'

            self._parse_attribute_part(line)

        elif self.state is State.NEW_ATTRIBUTE:
            # Whenever a new atribute is encountered the
            # following steps are executed
            #
            # (1) Parse possible compositions and foreign types
            # (2) Add the attribute to the object --> Triggers checks for mandatory options
            # (3) Sets up a new attribute that will be filled with options

            self._check_compositions()
            self._add_attribute_to_obj()
            self._set_up_new_attribute(line)

        elif self.state is State.NEW_ENUM:

            if hasattr(self, "enum"):
                self.enums.append(self.enum)

            self.enum = {
                "name": line.replace("#", "").strip(),
                "mappings": [],
                "docstring": [],
            }
            self.state = State.INSIDE_ENUM

        elif self.state is State.INSIDE_ENUM:
            if line.strip() and not line.startswith("'''"):
                self.enum["docstring"].append(line.strip())

        elif self.state is State.NEW_ENUM_VALUE:
            self.enum["mappings"].append(line.strip())

        elif self.state is State.END_OF_FILE:
            # When the file has ende, usually there will be a "leftover"
            # attribute. This will be addd here and the object put into
            # the list of all objects from the module

            self.obj["attributes"].append(self.attr.copy())
            self.objs.append(self.obj.copy())

    def _parse_object_name(self, line: str, index: int):
        """Checks and parses the object (### ObjectName) for a name and possible inheritance."""

        name = re.findall(OBJECT_NAME_PATTERN, line)[0]
        parent = re.findall(SUPER_PATTERN, line)

        if not name:
            raise ValueError(
                "".join(
                    [
                        f"No object name avalaible at \033[1mline {index}\033[0m. ",
                        f"Please make sure to enter objects by using the following: \033[1m### ObjectName\033[0m",
                    ]
                )
            )
        else:
            self.obj["name"] = name

        if parent:
            self.inherits.append({"parent": parent[0], "child": self.obj["name"]})

    def _parse_attribute_part(self, line):
        """Extracts the key value relation of an attribute option (e.g. 'Type : string')"""
        line = line.strip()

        key, value = re.findall(OPTION_PATTERN, line)[0]

        if bool(re.match(LINKED_TYPE_PATTERN, value)) and key == "Type":
            # Markdown linked types
            types = re.findall(LINKED_TYPE_PATTERN, value)[0].split(",")
            types = [dtype.strip() for dtype in types]

            if len(types) > 1:
                value = f"Union[{','.join(types)}]"
            else:
                value = types[0]

        elif key == "Type":
            # Non Markdown-linked types
            if "@" in line and "github.com" in line:
                # Catch external objects
                github_link, obj = self._fetch_external_object(line)
                self.external_objects[obj] = github_link[0]
                types = [obj]
            else:
                types = [dtype.strip() for dtype in value.split(",")]

            if len(types) > 1:
                value = f"Union[{','.join(types)}]"
            else:
                value = types[0]

        elif key.lower() == "multiple" and value == "False":
            return

        self.attr[key.lower()] = value

    def _check_compositions(self):
        """Checks for composition patterns and non-native types"""
        if not self.attr.get("type"):
            return None

        dtypes = self.attr["type"].replace("Union[", "").replace("]", "")
        for dtype in dtypes.split(","):
            if dtype not in DataTypes.__members__ and not dtype.startswith("@"):
                self.compositions.append(
                    {"module": dtype, "container": self.obj["name"]}
                )

    @staticmethod
    def _strip_references(dtype: str):
        """Removes reference syntax for composition entries to maintain Mermaid functionality"""
        return dtype.replace("@", "").split(".")[0]

    def _add_attribute_to_obj(self):
        """Adds an attribute to an object only IF the mandatory fields are given.

        This method will perform a content checkup that includes all mandatory
        fields such as 'Type' and 'Description' without which a code generation
        is infeasible. Raises an error with report if tests fail.
        """

        if self.attr.get("name") and self.attr["name"] in FORBIDDEN_NAMES:
            # Prevents forbidden names to be used and adds it to the
            # given alias of a fields.

            self.attr["alias"] = self.attr["name"]
            self.attr["name"] = f"{self.attr['name']}_"

        if self._check_mandatory_options() and self.attr:
            self.obj["attributes"].append(self.attr.copy())

        elif self.attr:
            missing_fields = list(
                filter(lambda option: option not in self.attr.keys(), MANDATORY_OPTIONS)
            )
            raise ValueError(
                "".join(
                    [
                        f"Missing mandatory fields for attribute \033[1m{self.attr['name']}\033[0m ",
                        f"in object \033[1m{self.obj['name']}\033[0m: {missing_fields}",
                    ]
                )
            )

        self.attr = {}

    def _check_mandatory_options(self) -> bool:
        """Checks if an attribute covers all mandatory fields/options"""
        return (
            all(option in self.attr.keys() for option in MANDATORY_OPTIONS)
            if self.attr
            else False
        )

    def _set_up_new_attribute(self, line):
        """Sets up a new attribute based on the Markdown definition '- __Name__'."""
        name, required = re.findall(ATTRIBUTE_PATTERN, line)[0]
        self.attr["name"] = name
        self.attr["required"] = required

    def __setattr__(self, key, value):
        """Overload of the set attribute method to signalize the end of the file"""
        if value is State.END_OF_FILE:
            self._add_attribute_to_obj()
            self.objs.append(self.obj.copy())

        super().__setattr__(key, value)

    def _fetch_external_object(self, type: str):

        splitted: List = type.split("@")
        pattern = re.compile(GITHUB_TYPE_PATTERN)

        if len(splitted) == 2:
            repo_link, obj = splitted[0], splitted[1]
        else:
            if bool(pattern.match(type)):
                raise ValueError(
                    f"GitHub URL missing the object specification using '@' - Example 'type@OBJECT'"
                )
            elif type.startswith("http") and not bool(bool(pattern.match(type))):
                raise ValueError(f"Given URL '{type}' is not a valid GitHub type.")
            else:
                raise ValueError(
                    f"Given Type is '{type}' is neither a valid GitHub link nor object specification"
                )

        return pattern.findall(repo_link), obj
