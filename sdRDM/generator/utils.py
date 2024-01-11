from enum import Enum
import inspect
import re

from sdRDM.base.importedmodules import ImportedModules
from sdRDM.tools.gitutils import ObjectNode


def camel_to_snake(name):
    """Turns a camel cased name into snake case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def extract_modules(lib, links) -> ImportedModules:
    """Extracts root nodes and specified modules from a generated API"""

    # Get all classes present
    classes = {
        obj.__name__: ObjectNode(obj)
        for obj in lib.__dict__.values()
        if inspect.isclass(obj) and not issubclass(obj, Enum)
    }

    enums = {
        obj.__name__: ObjectNode(obj)
        for obj in lib.__dict__.values()
        if inspect.isclass(obj) and issubclass(obj, Enum)
    }

    return ImportedModules(classes=classes, enums=enums, links=links)
