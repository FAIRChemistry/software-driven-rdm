import inspect
import json
import os
import h5py
import pydantic
import random
import tempfile
import toml
import validators
import yaml
import warnings
import numpy as np

from nob import Nob
from enum import Enum
from anytree import RenderTree, Node, LevelOrderIter
from h5py._hl.files import File as H5File
from h5py._hl.dataset import Dataset as H5Dataset
from lxml import etree
from pydantic import PrivateAttr, validator
from sqlalchemy.orm import declarative_base
from typing import Dict, Optional, IO, Union

from sdRDM.base.importemodules import ImportedModules
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import object_to_orm, generate_model
from sdRDM.base.ioutils.xml import write_xml
from sdRDM.base.ioutils.hdf5 import read_hdf5, write_hdf5
from sdRDM.linking.link import convert_data_model
from sdRDM.generator.codegen import generate_python_api
from sdRDM.linking.utils import build_guide_tree, generate_template
from sdRDM.database.utils import add_to_database
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
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        orm_mode = True

    # * Private attributes
    __node__: Optional[Node] = PrivateAttr(default=None)

    # ! Getters
    def get(
        self, path: str, attribute: Optional[str] = None, target: Optional[str] = None
    ):
        """Traverses the data model tree by a path or key and returns its content.

        Args:
            path (str): _description_
        """

        if not path.startswith("/") and len(path.split("/")) > 1:
            path = f"/{path}"

        model = Nob(self.to_dict(warn=False, convert_h5ds=False))
        path = model.find(path)

        if attribute is None and target is None:
            return self._traverse_model_by_path(self, path[0])
        else:
            object = self._traverse_model_by_path(self, path[0])

            if isinstance(object, ListPlus):
                result = object.get(query=target, attr=attribute)  # type: ignore

                if len(result) == 1:
                    return result[0]
                else:
                    return result

            else:
                if hasattr(object, attribute) and getattr(object, attribute) == target:
                    return object

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

    def paths(self, leaves: bool = False):
        """Returns all possible paths of an instantiated data model. Can also be reduced to just leaves."""

        # Get JSON representation
        model = Nob(self.to_dict(warn=False))

        if leaves:
            return model.leaves
        else:
            return model.paths

    @classmethod
    def meta_paths(cls, leaves: bool = False):
        """Returns all possible paths of an instantiated data model. Can also be reduced to just leaves."""

        metapaths = set()
        for node in LevelOrderIter(cls.create_tree()[0]):
            if len(node.path) == 1:
                continue

            if leaves and node.is_leaf:
                metapaths.add(
                    "/".join([n.name for n in node.path if n.name[0].islower()])
                )
            elif not leaves:
                metapaths.add(
                    "/".join([n.name for n in node.path if n.name[0].islower()])
                )

        return sorted(metapaths, key=lambda path: len(path.split("/")))

    # ! Exporters
    def to_dict(self, exclude_none=True, warn=True, convert_h5ds=True, **kwargs):
        data = super().dict(exclude_none=exclude_none, by_alias=True, **kwargs)

        # Convert all ListPlus items back to normal lists
        # to stay compliant to PyDantic
        data = self._convert_types(data, exclude_none, convert_h5ds)

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

    def _convert_types(self, data, exclude_none, convert_h5ds):
        """Converts als ListPlus items back to lists."""

        nu_data = {}

        for key, value in data.items():

            if isinstance(value, ListPlus):
                if not value and exclude_none:
                    continue

                nu_data[key] = [
                    self._check_and_convert_sub(element, exclude_none, convert_h5ds)
                    for element in value
                ]

            elif isinstance(value, (dict)):
                if not value and exclude_none:
                    continue

                if self._convert_types(value, exclude_none, convert_h5ds):
                    nu_data[key] = self._convert_types(
                        value, exclude_none, convert_h5ds
                    )

            elif isinstance(value, H5Dataset) and convert_h5ds:
                nu_data[key] = value[:].tolist()

            elif isinstance(value, np.ndarray):
                nu_data[key] = value.tolist()

            else:
                nu_data[key] = value

        return nu_data

    def _check_and_convert_sub(self, element, exclude_none, convert_h5ds):
        """Helper function used to trigger recursion on deeply nested lists."""

        if isinstance(element, np.ndarray):
            return element

        if element.__class__.__module__ == "builtins" and not isinstance(element, dict):
            return element

        return self._convert_types(element, exclude_none, convert_h5ds)

    def json(self, indent: int = 2):
        return json.dumps(self.to_dict(), indent=indent, default=self._json_dump)

    @staticmethod
    def _json_dump(value):
        """Helper function to export nd-arrays in a proper way"""

        if isinstance(value, np.ndarray):
            return value.tolist()

        return str(value)

    def yaml(self):
        return yaml.dump(
            self.to_dict(), Dumper=YAMLDumper, default_flow_style=False, sort_keys=False
        )

    def xml(self, pascal: bool = True):
        tree = write_xml(self, pascal=pascal)

        try:
            tree.attrib.update(
                {
                    "repo": self.__repo__,  # type: ignore
                    "commit": self.__commit__,  # type: ignore
                    "url": self.__repo__.replace(".git", f"/tree/{self.__commit__}"),  # type: ignore
                }
            )
        except AttributeError:
            pass

        return etree.tostring(
            tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")

    def hdf5(self, file: Union[H5File, str]) -> None:
        """Writes the object instance to HDF5."""
        write_hdf5(self, file)

    def convert_to(self, option: str = "", template: Union[str, None, Dict] = None):
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

        if isinstance(template, str):
            if template.lower().endswith(".yaml") or template.lower().endswith(".yml"):
                template = yaml.safe_load(open(template))
            elif template.lower().endswith("toml"):
                template = toml.load(open(template))
            else:
                raise TypeError(
                    f"Linking template format of '{template.split('.')[-1]}' is not supported. Please consider using TOML or YAML."
                )
        elif template is None:
            template = {}

        return convert_data_model(obj=self, option=option, template=template)

    def to_sql(self, loc: str):
        """Adds data to a complementary SQL database"""
        add_to_database(self, loc)

    @classmethod
    def build_orm(cls):
        """Builds an ORM model to build a database and fetch from"""

        Base = declarative_base()
        object_to_orm(cls, Base)

        return Base

    @classmethod
    def generate_linking_template(
        cls, path: str = "linking_template.toml", simple: bool = True
    ):
        """Generates a template that can be used to link between two data models."""

        generate_template(cls, path, simple)

    # ! Inherited Initializers
    @classmethod
    def from_dict(cls, obj: Dict):
        return cls.parse_obj(obj)

    @classmethod
    def from_json_string(cls, json_string: str):
        return cls.from_dict(json.loads(json_string))

    @classmethod
    def from_json(cls, handler: IO):
        return cls.from_dict(json.load(handler))

    @classmethod
    def from_yaml_string(cls, yaml_string: str):
        return cls.from_dict(yaml.safe_load(yaml_string))

    @classmethod
    def from_yaml(cls, handler: IO):
        return cls.from_dict(yaml.safe_load(handler))

    @classmethod
    def from_xml_string(cls, xml_string: str):
        raise NotImplementedError()

    @classmethod
    def from_hdf5(cls, file: h5py.File):
        """Reads a hdf5 file from path into the class model."""
        return read_hdf5(cls, file)

    # ! Dynamic initializers
    @classmethod
    def parse(
        cls,
        path: Optional[str] = None,
        data: Optional[Dict] = None,
        root_name: str = "Root",
        attr_replace: str = "",
    ):
        """Reads an arbitrary format and infers the corresponding object model to load the data.

        This function is used to open legacy files or any other file where the software
        is not known. In addition, this function allows you to load any sdRDM capable
        format without having to install a library.

        Args:
            path (str): Path to the file to load.
            data (Dict): Dataset in dict format.
            root_name (str): Name of the root element. Defaults to 'Root'
            attr_replace (str): When the given data model keys contain a pattern to replace for readability. Defaults to empty string.
        """

        # Detect base
        if path and data is None:
            if cls._is_json(path):
                dataset = json.loads(open(path).read())
            elif cls._is_yaml(path):
                dataset = yaml.safe_load(open(path).read())
            elif cls._is_hdf5(path):
                import deepdish as dd

                dataset = dd.io.load(path)
            else:
                raise TypeError("Base format is unknown!")
        elif data and path is None:
            dataset = data
        elif data and path:
            raise ValueError(
                f"Data and path have been specified. Please use only one of the arguments to parse live data ('data') or file data ('path')"
            )
        else:
            raise ValueError(
                f"Neither path nor data have been specified. Either of both should be specified."
            )

        # Check if there is a source reference
        if "__source__" not in dataset:
            # If no source is given, just create a model
            # from the blank dataset -> Can be incomplete
            lib = generate_model(
                data=dataset,
                name=root_name,
                base=cls,
                attr_replace=attr_replace,
            )
            root = getattr(lib, root_name)
            return root.from_dict(dataset), lib
        else:
            # Get source and build libary
            url = dataset.get("__source__")["repo"]
            commit = dataset.get("__source__")["commit"]
            root = dataset.get("__source__")["root"]
            lib = cls.from_git(url=url, commit=commit)

            # Use the internal librar to parse the file
            return getattr(lib, root).from_dict(dataset), lib  # type: ignore

    @staticmethod
    def _is_json(path: str):
        try:
            json.loads(open(path).read())
        except ValueError as e:
            return False
        return True

    @staticmethod
    def _is_yaml(path: str):
        try:
            yaml.safe_load(open(path).read())
        except ValueError as e:
            return False
        return True

    @staticmethod
    def _is_hdf5(path: str):
        import deepdish as dd
        from tables.exceptions import HDF5ExtError

        try:
            dd.io.load(path)
        except HDF5ExtError as e:
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
            generate_python_api(
                path=path, out=tmpdirname, name=lib_name, use_formatter=False
            )

            lib = _import_library(api_loc, lib_name)

        return cls._extract_modules(lib=lib, links={})

    @classmethod
    def from_git(
        cls,
        url: str,
        commit: Optional[str] = None,
        tag: Optional[str] = None,
        only_classes: bool = False,
    ):
        """Fetches a Markdown specification from a git repository and builds the library accordingly.

        This function will clone the repository into a temporary directory and
        builds the correpsonding API and loads it into the memory. After that
        the cloned repository is deleted and the root object(s) detected.

        Args:
            url (str): Link to the git repository. Use the URL ending with ".git".
            commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
            tag (Optional[str], optional): Tag of the release or branch to fetch from. Defaults to None.
        """

        if not validators.url(url):
            raise ValueError(f"Given URL '{url}' is not a valid URL.")

        # Build and import the library
        lib, links = build_library_from_git_specs(
            url=url, commit=commit, tag=tag, only_classes=only_classes
        )

        if only_classes:
            return lib

        return cls._extract_modules(lib, links)

    @classmethod
    def _extract_modules(cls, lib, links):
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

        return ImportedModules(classes, enums, links)

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
    def to_dataverse(self, template: Optional[str] = None):
        """
        Converts a dataset to it Datavere specifications and returns a Dataset object,
        which can be uploaded to Dataverse.
        """

        from easyDataverse import Dataset

        blocks = self.convert_to("dataverse", template=template)

        if not blocks:
            raise ValueError("Couldnt convert, no mapping towards Dataverse specified.")

        dataset = Dataset()
        for block in blocks:
            dataset.add_metadatablock(block[0])

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
    @validator("*")
    def convert_extended_list_and_numpy_strings(cls, value):
        """Validator used to convert any list into a ListPlus."""
        if isinstance(value, list):
            return ListPlus(*[cls._convert_numpy_type(v) for v in value], in_setup=True)
        elif isinstance(value, np.str_):
            return str(value)
        else:
            return value

    @staticmethod
    def _convert_numpy_type(value):
        """Helper function to convert numpy strings into builtin"""
        if isinstance(value, np.str_):
            return str(value)

        return value
