import ast
import re

from enum import Enum, auto

# Constants
REFERENCE_PATTERN = r"get_[A-Za-z0-9\_]*_reference"
ADDER_PATTERN = r"add_to_[A-Za-z0-9\_]*"
INHERITANCE_PATTERN = r"class [A-Za-z0-9\_\.]*\(([A-Za-z0-9\_\.]*)\)\:"

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
    """When a class has alreay been written and modified, this function
    will read the original script and accordingly change only attributes
    and data model related methods, while preserving custom methods.

    Args:
        rendered_class (str): The newly generated class
        path (str): Path to the previous file
    """

    # Turn the rendered class into an Abstract Syntax Tree and get the class
    new_module = ast.parse(rendered_class)
    previous_module = ast.parse(open(path).read())
    
    # Format data model class
    _format_classes(new_module, previous_module)

    # Format and merge imports
    _format_imports(new_module, previous_module)

    return _stylize_class(ast.unparse(previous_module))

def _stylize_class(rendered: str):
    """Inserts newlines to render the code more readable"""
    
    if "Enum" in rendered:
        return rendered
    
    nu_render = []
    for line in rendered.split("\n"):
        if bool(re.findall(r"[Field|PrivateAttr]", line)) and ": " in line:
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

def _format_classes(new_module, previous_module):
    """Re-formats a given class to preserve custom functions that would otherwise be overwritten"""

    # Return the new class from the module
    new_class = next(
        filter(lambda element: isinstance(element, ast.ClassDef), new_module.body)  # type: ignore
    )

    # Get all the attributes present in the new module
    new_attributes = {
        attr.target.id: attr
        for attr in new_class.body
        if isinstance(attr, ast.AnnAssign)
    }
    
    new_enums = {
        enum.targets[0].id: enum
        for enum in new_class.body
        if isinstance(enum, ast.Assign)
    }

    new_methods = {
        method.name: method
        for method in new_class.body
        if isinstance(method, ast.FunctionDef)
    }
    # Load the previous script as an AST
    previous_class = next(
        filter(lambda element: isinstance(element, ast.ClassDef), previous_module.body)  # type: ignore
    )

    # Iterate over the old syntax tree and delete/add where necessary
    nu_body = []
    for element in previous_class.body:
        if isinstance(element, ast.AnnAssign):
            # If the attribute is part of the new module, add it
            if (
                element.target.id in new_attributes
                and ast.unparse(element) == ast.unparse(new_attributes[element.target.id])
            ):
                del new_attributes[element.target.id]
            else:
                continue
            
        elif isinstance(element, ast.Assign):
            # If the enum value is part of the new module, add it
            if element.targets[0].id in new_enums:
                del new_enums[element.targets[0].id]
            else:
                continue

        elif isinstance(element, ast.FunctionDef):
            # If the method is part of the new module, add it
            if bool(re.match(ADDER_PATTERN, element.name)):
                # Skip adder functions
                continue
            elif bool(re.match(REFERENCE_PATTERN, element.name)):
                # Skip generated reference getters
                continue
            elif element.name in new_methods:
                if ast.unparse(element) != ast.unparse(new_methods[element.name]):
                    element = new_methods[element.name]

                del new_methods[element.name]
            else:
                continue

        nu_body.append(element)

    # Add the remaining attributes and methods
    nu_body += list(new_attributes.values())
    nu_body += list(new_methods.values())
    nu_body += list(new_enums.values())

    # Set the new body for the class
    previous_class.body = sorted(nu_body, key=_sort_class_body)


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


def _format_imports(new_module, previous_model):
    """Formats given inputs and merges the new imports to the previous ones"""

    # Get all imports
    new_imports = [
        element
        for element in new_module.body
        if isinstance(element, (ast.ImportFrom, ast.Import))
    ]
    
     # Check if inheritance is given
    inherited_class = re.findall(INHERITANCE_PATTERN, ast.unparse(new_module))[0]

    types = _get_module_types(new_module)
    previous_model.body += new_imports

    used_imports = set()
    nu_body = []
    
    for element in previous_model.body:
        
        if ast.unparse(element) in used_imports:
            continue
        
        if isinstance(element, (ast.Import, ast.ImportFrom)):
            imp = ast.unparse(element)
            
            if "from ." in imp:
                if element.names[0].name == inherited_class:
                    used_imports.add(ast.unparse(element))
                elif element.names[0].name not in types:
                    continue
                elif imp not in used_imports:
                    # Add unique import
                    used_imports.add(ast.unparse(element))
                else:
                    continue
            else:
                used_imports.add(ast.unparse(element))

        nu_body.append(element)        

    previous_model.body = sorted(nu_body, key=_sort_module)

def _get_module_types(module):
    """Parses an AST module and returns all types that are used and need to be imported"""

    types = set()
    for element in module.body:

        if isinstance(
            element, (ast.Import, ast.ImportFrom)
        ) and "from ." not in ast.unparse(element):
            types.add(element.names[0].name)

        elif isinstance(element, ast.ClassDef):
            types.update(_get_cls_types(element))

    return types


def _get_cls_types(cls_obj):
    """Retrieves all types found in a class"""

    types = set()
    for element in cls_obj.body:

        if isinstance(element, ast.AnnAssign):
            if hasattr(element.annotation, "slice"):
                # Parse nested types such as List[SomeType]
                try:
                    types.add(element.annotation.slice.id)
                except AttributeError:
                    # Preserve imports from Union Types
                    for dtype in element.annotation.slice.elts:
                        if hasattr(dtype, "id"):
                            types.add(dtype.id)
            else:
                # Parse lone attributes
                types.add(element.annotation.id)

        elif isinstance(element, ast.FunctionDef):
            for arg in element.args.args:
                annotation = arg.annotation

                if annotation and hasattr(annotation, "slice"):
                    try:
                        types.add(arg.annotation.slice.id)
                    except AttributeError:
                        # Preserve imports from Union Types
                        for dtype in arg.annotation.slice.elts:
                            if hasattr(dtype, "id"):
                                types.add(dtype.id)
                            
                elif annotation:
                    types.add(annotation.id)
    
    return types

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
        