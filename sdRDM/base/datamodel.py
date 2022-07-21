import xmltodict
import json
import yaml
import deepdish as dd
import pydantic

from anytree import RenderTree

from sdRDM.linking.link import convert_data_model_by_option
from sdRDM.linking.utils import build_guide_tree


class DataModel(pydantic.BaseModel):
    class Config:
        validate_assignment = True
        use_enum_values = True

    # ! Exporters

    def json(self, indent: int = 2):
        return super().json(exclude_none=True, indent=indent)

    def yaml(self):
        class MyDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super(MyDumper, self).increase_indent(flow, False)

        return yaml.dump(
            self.dict(), Dumper=MyDumper, default_flow_style=False, sort_keys=True
        )

    def xml(self, to_string=True):
        return xmltodict.unparse(
            {self.__class__.__name__: self.dict(exclude_none=True)},
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

    # ! Initializers

    @classmethod
    def from_dict(cls, obj: dict):
        return cls.parse_obj(obj)

    @classmethod
    def from_json_string(cls, json_string: str):
        return cls.from_dict(json.loads(json_string))

    @classmethod
    def from_xml_string(cls, xml_string: str):
        raise NotImplementedError()

    @classmethod
    def from_hdf5(cls, path: str):
        """Reads a hdf5 file from path into the class model"""
        return cls.from_dict(dd.io.load(path))

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
            dataset.add_metadatablock(block)

        return dataset

    # ! Utilities

    @classmethod
    def create_tree(cls):
        """Builds a tree structure from the class definition and all decending types."""

        tree = build_guide_tree(cls)

        return tree, RenderTree(tree)
