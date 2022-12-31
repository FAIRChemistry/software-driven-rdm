import re

from typing import List, Union

from redbaron import RedBaron
from redbaron.nodes import ImportNode, FromImportNode, CommaNode


def camel_to_snake(name):
    """Turns a camel cased name into snake case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def clean_imports(imports: str, cls_body: str) -> str:
    """
    Parses given imports using a Full Syntax Tree and remove those that do not occur within the code.
    """

    import_tree = RedBaron(imports)
    remove_nodes = []
    nu_nodes = []

    for i, node in enumerate(import_tree):
        if not isinstance(node, (FromImportNode, ImportNode)):
            continue

        if isinstance(node, FromImportNode):
            names = get_import_names(node)
            to_remove = [name for name in names if name not in cls_body]
            nu_import = clean_from_import(node.targets, to_remove)

            if not nu_import.strip():
                del import_tree[i]
            else:
                node.targets = nu_import

        elif isinstance(node, ImportNode):
            to_remove = [name for name in node.names() if name not in cls_body]

            if to_remove:
                del import_tree[i]

    # Remove initial blank lines
    import_tree.first_blank_lines = []

    return import_tree.dumps().strip()


def clean_from_import(targets: FromImportNode, to_remove: List[str]) -> str:
    """Removes import statements from"""

    return ", ".join(
        [target.value for target in targets if target.value not in to_remove]
    )


def get_import_names(node: Union[ImportNode, FromImportNode]) -> List[str]:
    """Gets all targets names of an import (native and from)"""
    return node.names()
