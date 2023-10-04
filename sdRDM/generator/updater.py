import ast
import re

from collections import defaultdict
from typing import List, Dict
from enum import Enum, auto

# Constants
REFERENCE_PATTERN = r"get_[A-Za-z0-9\_]*_reference"
ADDER_PATTERN = r"add_to_[A-Za-z0-9\_]*"
INHERITANCE_PATTERN = r"class [A-Za-z0-9\_\.]*\(([A-Za-z0-9\_\.]*)\)\:"
ATTRIBURE_PATTERN = r"description=(\"|\')[A-Za-z0-9\_\.]*"
FUNCTION_PATTERN = r"def ([a-zA-Z0-9_]+)\("
FUNCTION_NAME_PATTERN = r"def ([a-zA-Z0-9_]+)\("


class ModuleOrder(Enum):
    IMPORT_SDRDM = auto()
    IMPORT_MISC = auto()

    FROM_TYPING = auto()
    FROM_PYDANTIC = auto()
    FROM_SDRDM = auto()
    FROM_MISC = auto()
    FROM_LOCAL = auto()

    CLASSES = auto()
    FUNCTIONS = auto()
    MISC = auto()


class ClassOrder(Enum):
    DOCSTRING = auto()
    ATTRIBUTES = auto()
    PRIV_ATTRIBUTES = auto()
    METHODS = auto()


def preserve_custom_functions(rendered_class: str, path: str) -> str:
    """When a class has already been written and modified, this function
    will read the original script and accordingly change only attributes
    and data model related methods, while preserving custom methods.

    Args:
        rendered_class (str): The newly generated class
        path (str): Path to the previous file
    """

    custom_methods = extract_custom_methods(rendered_class, path)

    # Turn the rendered class into an Abstract Syntax Tree and get the class
    new_module = ast.parse(rendered_class)
    previous_module = ast.parse(open(path).read())

    # Format and merge imports
    _format_imports(new_module, previous_module)

    # Get the class body
    new_class = _stylize_class(ast.unparse(new_module))

    # Merge the previous custom methods with the new class
    return "\n".join([new_class, custom_methods])


def extract_custom_methods(rendered_class: str, path: str) -> List[str]:
    with open(path, "r") as file:
        previous_class = file.read().split("\n")
    custom_method_names = get_custom_method_names(rendered_class, previous_class)

    # Identify lines where functions start and end
    method_starts = [
        line_count
        for line_count, line in enumerate(previous_class)
        if re.findall(FUNCTION_PATTERN, line)
    ]

    method_ends = [fun_start - 1 for fun_start in method_starts[1:]]
    method_ends.append(len(previous_class))

    # Create slices for each function that is not part of the new class
    methods = []
    for method_name in custom_method_names:
        for start, end in zip(method_starts, method_ends):
            if method_name in previous_class[start]:
                methods.append("\n".join(previous_class[start:end]))

    return "\n".join(methods)


def get_custom_method_names(rendered_class: str, previous_class: str) -> List[str]:
    """Returns the names of custom functions that exist in the previous class"""

    generated_methods = []
    for line in rendered_class.split("\n"):
        if not bool(re.findall(FUNCTION_PATTERN, line)):
            continue

        generated_methods.append(re.findall(FUNCTION_NAME_PATTERN, line)[0])

    previous_methods = []
    for line in previous_class:
        if not bool(re.findall(FUNCTION_PATTERN, line)):
            continue

        previous_methods.append(re.findall(FUNCTION_NAME_PATTERN, line)[0])

    custom_methods = [
        method for method in previous_methods if method not in generated_methods
    ]

    return custom_methods


def _stylize_class(rendered: str):
    """Inserts newlines to render the code more readable"""

    if "Enum" in rendered:
        return rendered

    nu_render = []
    for line in rendered.split("\n"):
        if bool(re.findall(r"[Field|PrivateAttr]", line)) and ": " in line:
            if bool(re.findall(ATTRIBURE_PATTERN, line)):
                nu_render.append("\n")

            nu_render.append(line)

        else:
            nu_render.append(line)

    return _insert_new_lines("\n".join(nu_render))


def _insert_new_lines(rendered: str):
    """Inserts new lines for imports"""
    rendered = rendered.replace("import sdRDM", "import sdRDM\n")
    split_index = rendered.find("@forge_signature")

    return f"{rendered[0:split_index]}\n{rendered[split_index::]}"


def _sort_class_body(element) -> int:
    """Sorts bodies of classes according to Expressions > Annotations > Methods"""

    if isinstance(element, (ast.Expression, ast.Expr)):
        return ClassOrder.DOCSTRING.value
    elif isinstance(element, ast.AnnAssign):
        if not element.target.id.startswith("__"):
            return ClassOrder.ATTRIBUTES.value
        else:
            return ClassOrder.PRIV_ATTRIBUTES.value
    elif isinstance(element, ast.Assign):
        return ClassOrder.ATTRIBUTES.value
    elif isinstance(element, ast.FunctionDef):
        return ClassOrder.METHODS.value
    else:
        raise ValueError(f"Unknown type {type(element)} in sort algorithm")


def _format_imports(new_module, previous_module):
    """Formats given inputs and merges previous imports to the new ones"""

    # Get all imports
    imports = []  # import ...
    from_imports = []  # from ... import ...

    # Get all imports from the new module
    for node in ast.walk(new_module):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.Import) and ast.unparse(node) not in [
            ast.unparse(imp) for imp in imports
        ]:
            imports.append(node)

        if isinstance(node, ast.Import):
            continue

        if ast.unparse(node) not in [ast.unparse(imp) for imp in from_imports]:
            from_imports.append(node)

    # Get all imports from the previous module
    for node in ast.walk(previous_module):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.Import) and ast.unparse(node) not in [
            ast.unparse(imp) for imp in imports
        ]:
            imports.append(node)

        if isinstance(node, ast.Import):
            continue

        if node.module not in [imp.module for imp in from_imports]:
            from_imports.append(node)
        else:
            # Add submodules to existing imports
            for imp in from_imports:
                if imp.module != node.module:
                    continue
                for sub_module in node.names:
                    if sub_module.name not in [submod.name for submod in imp.names]:
                        imp.names.append(sub_module)

    # Add modified imports to the new module
    nu_body = []
    for element in new_module.body:
        if isinstance(element, (ast.Import, ast.ImportFrom)):
            continue

        nu_body.append(element)

    nu_body += imports + from_imports

    new_module.body = sorted(nu_body, key=_sort_module)


def _sort_module(element):
    """Sorts module Imports > Classes > Functions"""

    if isinstance(element, ast.Import):
        if "sdRDM" in ast.unparse(element):
            return ModuleOrder.IMPORT_SDRDM.value
        else:
            return ModuleOrder.IMPORT_MISC.value
    elif isinstance(element, ast.ImportFrom):
        if "from ." in ast.unparse(element):
            return ModuleOrder.FROM_LOCAL.value
        elif element.module == "typing":
            return ModuleOrder.FROM_TYPING.value
        elif element.module == "pydantic":
            return ModuleOrder.FROM_PYDANTIC.value
        elif element.module == "sdRDM":
            return ModuleOrder.FROM_SDRDM.value
        else:
            return ModuleOrder.FROM_MISC.value
    elif isinstance(element, ast.ClassDef):
        return ModuleOrder.CLASSES.value
    elif isinstance(element, ast.FunctionDef):
        return ModuleOrder.FUNCTIONS.value
    else:
        return ModuleOrder.MISC.value
