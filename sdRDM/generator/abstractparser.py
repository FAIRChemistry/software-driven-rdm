from abc import ABC, abstractclassmethod
from typing import List


class SchemaParser(ABC):

    objs: List
    inherits: List
    compositions: List
    module_name: str = ""
    module_docstring: List[str]

    @abstractclassmethod
    def parse(cls, path: str):
        raise NotImplementedError()
