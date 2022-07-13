import xmltodict
import json
import yaml
import deepdish as dd
import pydantic

from anytree import RenderTree

from sdRDM.linking.treeutils import build_guide_tree


class DataModel(pydantic.BaseModel):
    class Config:
        validate_assignment = True
        use_enum_values = True

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

    def create_tree(self):
        """Builds a tree structure from the class definition and all decending types."""

        tree = build_guide_tree(self.__class__)

        return tree, RenderTree(tree)
