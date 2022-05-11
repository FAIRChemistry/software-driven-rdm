import xmltodict
import json
import yaml
import deepdish as dd
import pydantic


from sdRDM.tools.xmltools import XMLWriter
from sdRDM.tools.utils import camel_to_snake, change_dict_keys


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
        cls_name = camel_to_snake(cls.__name__)
        obj = dict(xmltodict.parse(xml_string, force_list=True))

        print(obj)

        print("RESULT", change_dict_keys(obj[cls.__name__][0], camel_to_snake))

        return cls.parse_obj(change_dict_keys(obj, camel_to_snake)[cls_name][0])

    @classmethod
    def from_hdf5(cls, path: str):
        """Reads a hdf5 file from path into the class model"""
        return cls.from_dict(dd.io.load(path))
