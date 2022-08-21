import inspect
import json
import deepdish as dd
import os
import pydantic
import random
import tempfile
import yaml
import warnings

from anytree import RenderTree, Node
from enum import Enum
from lxml import etree
from nob import Nob
from pydantic import PrivateAttr, root_validator, validator
from typing import Dict, Iterable, Optional

from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import build_xml
from sdRDM.linking.link import convert_data_model
from sdRDM.generator.codegen import generate_python_api
from sdRDM.linking.utils import build_guide_tree, generate_template
from sdRDM.tools.utils import YAMLDumper
from sdRDM.tools.gitutils import (
    ObjectNode,
    build_library_from_git_specs,
    _import_library,
)


class DataModel(pydantic.BaseModel):
    class Config:
        validate_assignment = True
        use_enum_values = True
        allow_population_by_field_name = True

    # * Private attributes
    __node__: Optional[Node] = PrivateAttr(default=None)

    # ! Getters
    def get(self, path: str):
        """Traverses the data model tree by a path or key and returns its content.

        Args:
            path (str): _description_
        """

        if not path.startswith("/"):
            path = f"/{path}"

        model = Nob(self.to_dict(warn=False))

        for path in model.find(path):
            return self._traverse_model_by_path(self, path)

    def _traverse_model_by_path(self, object, path):
        """Traverses a give sdRDM model by using a path"""

        if path[0].isdigit():
            object = object[int(path[0])]
        else:
            object = getattr(object, path[0])

        if len(path) == 1:
            return object
        else:
            return self._traverse_model_by_path(object, path[1::])

    # ! Exporters
    def to_dict(self, exclude_none=True, warn=True):
        data = super().dict(exclude_none=exclude_none, by_alias=True)

        # Convert all ListPlus items back to normal lists
        # to stay compliant to PyDantic
        data = self._convert_to_lists(data, exclude_none)

        # Add source for reproducibility
        data["__source__"] = {"root": self.__class__.__name__}

        try:
            # Add git specs if available
            data["__source__"].update(
                {
                    "repo": self.__repo__,  # type: ignore
                    "commit": self.__commit__,  # type: ignore
                    "url": self.__repo__.replace(".git", "") + f"/tree/{self.__commit__}",  # type: ignore
                }
            )  # type: ignore
        except AttributeError:
            if warn:
                warnings.warn(
                    "No 'URL' and 'Commit' specified. This model might not be re-usable."
                )

        return data

    def _convert_to_lists(self, data, exclude_none):
        """Converts als ListPlus items back to lists."""

        nu_data = {}

        for key, value in data.items():
            if isinstance(value, ListPlus):
                if not value and exclude_none:
                    continue

                nu_data[key] = [
                    self._check_and_convert_sub(element, exclude_none)
                    for element in value
                ]

            elif isinstance(value, dict):
                if not value and exclude_none:
                    continue

                if self._convert_to_lists(value, exclude_none):
                    nu_data[key] = self._convert_to_lists(value, exclude_none)

            else:
                nu_data[key] = value

        return nu_data

    def _check_and_convert_sub(self, element, exclude_none):
        """Helper function used to trigger recursion on deeply nested lists."""

        if element.__class__.__module__ == "builtins" and not isinstance(element, dict):
            return element

        return self._convert_to_lists(element, exclude_none)

    def json(self, indent: int = 2):
        return json.dumps(self.to_dict(), indent=indent)

    def yaml(self):
        return yaml.dump(
            self.to_dict(), Dumper=YAMLDumper, default_flow_style=False, sort_keys=True
        )

    def xml(self, to_string=True):
        tree = build_xml(self)
        tree.attrib.update(
            {
                "repo": self.__repo__,  # type: ignore
                "commit": self.__commit__,  # type: ignore
                "url": self.__repo__.replace(".git", f"/tree/{self.__commit__}"),  # type: ignore
            }
        )

        return etree.tostring(
            tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")

    def hdf5(self, path: str) -> None:
        """Writes the object instance to HDF5."""
        dd.io.save(path, self.to_dict())

    def convert_to(self, option: str = "", linking_template: Optional[str] = None):
        """
        Converts a given data model to another model that has been specified
        in the attributes metadata. This will create a new object model from
        the current.

        Example:
            ## Origin
            class DataModel(sdRDM.DataModel):
                foo: str = Field(... another_model="AnotherModel.sub.bar")

            --> The goal is to project the data from 'DataModel' to 'AnotherModel'
                which maps the 'foo' attribute to the nested 'bar' attribute.

        This function provides the utility to map in between data models and
        offer an exchange of data without explicit code.

        Args:
            option (str): Key of the attribute metadata, where the destination is stored.
        """

        return convert_data_model(obj=self, option=option, path=linking_template)

    @classmethod
    def generate_linking_template(cls, path: str = "linking_template.yaml"):
        """Generates a template that can be used to link between two data models."""

        generate_template(cls, path)

    # ! Inherited Initializers
    @classmethod
    def from_dict(cls, obj: Dict):
        return cls.parse_obj(obj)

    @classmethod
    def from_json_string(cls, json_string: str):
        return cls.from_dict(json.loads(json_string))

    @classmethod
    def from_json(cls, path: str):
        return cls.from_dict(json.load(open(path)))

    @classmethod
    def from_xml_string(cls, xml_string: str):
        raise NotImplementedError()

    @classmethod
    def from_hdf5(cls, path: str):
        """Reads a hdf5 file from path into the class model"""
        return cls.from_dict(dd.io.load(path))

    # ! Dynamic initializers
    @classmethod
    def parse(cls, path: str):
        """Reads an arbitrary format and infers the corresponding object model to load the data.

        This function is used to open legacy files or any other file where the software
        is not known. In addition, this function allows you to load any sdRDM capable
        format without having to install a library.

        Args:
            path (str): Path to the file to load.
        """

        # Read the file
        raw_dataset = open(path).read()

        # Detect base
        if cls._is_json(raw_dataset):
            dataset = json.loads(raw_dataset)
        else:
            raise TypeError("Base format is unknown!")

        # Check if there is a source reference
        if "__source__" not in dataset:
            raise ValueError("Source reference is missing!")

        # Get source and build libary
        url = dataset.get("__source__")["repo"]
        commit = dataset.get("__source__")["commit"]
        root = dataset.get("__source__")["root"]
        lib = cls.from_git(url=url, commit=commit)

        # Use the internal librar to parse the file
        return getattr(lib, root).from_dict(dataset)  # type: ignore

    @staticmethod
    def _is_json(json_string: str):
        try:
            json.loads(json_string)
        except ValueError as e:
            return False
        return True

    @classmethod
    def from_markdown(cls, path: str):
        """Fetches a Markdown specification from a git repository and builds the library accordingly.

        This function will clone the repository into a temporary directory and
        builds the correpsonding API and loads it into the memory. After that
        the cloned repository is deleted and the root object(s) detected.

        Args:
            url (str): Link to the git repository. Use the URL ending with ".git".
            commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
        """

        with tempfile.TemporaryDirectory() as tmpdirname:
            # Generate API to parse the file
            lib_name = f"sdRDM-Library-{str(random.randint(0,30))}"
            api_loc = os.path.join(tmpdirname, lib_name)
            generate_python_api(path=path, out=tmpdirname, name=lib_name)

            lib = _import_library(api_loc, lib_name)

        return cls._extract_modules(lib)

    @classmethod
    def from_git(
        cls,
        url: str,
        commit: Optional[str] = None,
    ):
        """Fetches a Markdown specification from a git repository and builds the library accordingly.

        This function will clone the repository into a temporary directory and
        builds the correpsonding API and loads it into the memory. After that
        the cloned repository is deleted and the root object(s) detected.

        Args:
            url (str): Link to the git repository. Use the URL ending with ".git".
            commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
        """

        # Build and import the library
        lib = build_library_from_git_specs(url=url, commit=commit)

        return cls._extract_modules(lib)

    @classmethod
    def _extract_modules(cls, lib):
        """Extracts root nodes and specified modules from a generated API"""

        # Get all classes present
        classes = {
            obj.__name__: ObjectNode(obj)
            for obj in lib.__dict__.values()
            if inspect.isclass(obj) and issubclass(obj, DataModel)
        }

        enums = {
            obj.__name__: ObjectNode(obj)
            for obj in lib.__dict__.values()
            if inspect.isclass(obj) and issubclass(obj, Enum)
        }

        class ImportedModules:
            """Empty class used to store all sub classes"""

            def __init__(self, classes, enums=None):
                for name, node in classes.items():
                    # Add all classes
                    setattr(self, name, node.cls)

                if enums:
                    self.enums = self.__class__(classes=enums)

        return ImportedModules(classes, enums)

    @staticmethod
    def _find_root_objects(classes: Dict):
        """Parses a given library and returns the root object(s)

        Root objects are assumed to be objects that are not part of
        another class yet possess other objects/attributes.
        """

        for definition in classes.values():
            for field in definition.cls.__fields__.values():
                if "Union" not in repr(field.type_) and issubclass(
                    field.type_, DataModel
                ):
                    classes[field.type_.__name__].add_parent_class(definition)

        roots = list(
            filter(lambda definition: not definition.parent_classes, classes.values())
        )

        return [root.cls for root in roots]

    # ! Databases
    def to_dataverse(self, linking_template: Optional[str] = None):
        """
        Converts a dataset to it Datavere specifications and returns a Dataset object,
        which can be uploaded to Dataverse.
        """

        from easyDataverse import Dataset

        blocks = self.convert_to("dataverse", linking_template=linking_template)

        if not blocks:
            raise ValueError("Couldnt convert, no mapping towards Dataverse specified.")

        dataset = Dataset()
        for block in blocks:
            dataset.add_metadatablock(block)

        return dataset

    # ! Utilities
    @classmethod
    def create_tree(cls):
        """Builds a tree structure from the class definition and all decending types."""
        tree = build_guide_tree(cls)
        return tree, RenderTree(tree)

    @classmethod
    def visualize_tree(cls):
        _, render = cls.create_tree()
        print(render.by_attr("name"))

    # ! Validators
    @root_validator(pre=True)
    def turn_into_extended_list(cls, values):
        """Validator used to convert any list into a ListPlus. On root level."""

        for field, value in values.items():
            if isinstance(value, list):
                values[field] = ListPlus(*value, in_setup=True)

        return values

    @validator("*")
    def turn_individual_value_into_extended_list(cls, value):
        """Validator used to convert any list into a ListPlus."""
        if isinstance(value, list):
            return ListPlus(*value, in_setup=True)
        else:
            return value
