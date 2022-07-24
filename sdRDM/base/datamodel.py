import inspect
import xmltodict
import json
import os
import yaml
import deepdish as dd
import pydantic

from anytree import RenderTree
from pydantic import PrivateAttr
from typing import Callable, Dict, Optional

from sdRDM.linking.link import convert_data_model_by_option
from sdRDM.linking.utils import build_guide_tree
from sdRDM.tools.gitutils import ObjectNode, build_library_from_git_specs
from sdRDM.tools.utils import YAMLDumper


class DataModel(pydantic.BaseModel):
    class Config:
        validate_assignment = True
        use_enum_values = True

    # ! Exporters
    def dict(self):
        data = super().dict(exclude_none=True)
        data["__source__"] = {"url": self.__url__, "commit": self.__commit__}

        return data

    def json(self, indent: int = 2):
        return json.dumps(self.dict(), indent=indent)

    def yaml(self):
        return yaml.dump(
            self.dict(), Dumper=YAMLDumper, default_flow_style=False, sort_keys=True
        )

    def xml(self, to_string=True):
        return xmltodict.unparse(
            {self.__class__.__name__: self.dict()},
            pretty=True,
            indent="    ",
        )

    def hdf5(self, path: str) -> None:
        """Writes the object instance to HDF5."""
        dd.io.save(path, self.dict())

    def convert(self, option: str):
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

        return convert_data_model_by_option(obj=self, option=option)

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
    def from_git(cls, url: str, commit: Optional[str] = None):
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

        # Find the corresponding root(s)
        roots = cls._find_root_objects(lib)

        if len(roots) == 1:
            return roots[0]

        return roots

    @staticmethod
    def _find_root_objects(lib: Callable):
        """Parses a given library and returns the root object(s)

        Root objects are assumed to be objects that are not part of
        another class yet possess other objects/attributes.
        """

        classes = {
            cls.__name__: ObjectNode(cls)
            for cls in lib.__dict__.values()
            if inspect.isclass(cls) and issubclass(cls, DataModel)
        }

        for definition in classes.values():
            for field in definition.cls.__fields__.values():
                if issubclass(field.type_, DataModel):
                    classes[field.type_.__name__].add_parent_class(definition)

        roots = list(
            filter(lambda definition: not definition.parent_classes, classes.values())
        )

        return [root.cls for root in roots]

    # ! Databases
    def to_dataverse(self):
        """
        Converts a dataset to it Datavere specifications and returns a Dataset object,
        which can be uploaded to Dataverse.
        """

        from easyDataverse import Dataset

        blocks = self.convert("dataverse")

        if not blocks:
            raise ValueError("Couldnt convert, no mapping towards Dataverse specified.")

        dataset = Dataset()
        for block in blocks:
            if block.dict(exclude_none=True):
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
