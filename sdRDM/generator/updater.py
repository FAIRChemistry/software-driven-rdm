import ast
import re
from typing import List, Tuple

# Constants
REFERENCE_PATTERN = r"get_[A-Za-z0-9\_]*_reference"
ADDER_PATTERN = r"add_to_[A-Za-z0-9\_]*"
INHERITANCE_PATTERN = r"class [A-Za-z0-9\_\.]*\(([A-Za-z0-9\_\.]*)\)\:"
ATTRIBURE_PATTERN = r"description=(\"|\')[A-Za-z0-9\_\.]*"
FUNCTION_PATTERN = r"(async\s+)?def\s+([a-zA-Z0-9_]+)\("
FUNCTION_NAME_PATTERN = r"def ([a-zA-Z0-9_]+)\("
XML_PARSER_PATTERN = r"_parse_raw_xml_data"
ANNOTATION_PATTERN = r"_validate_annotation"


def preserve_custom_functions(rendered: str, existing_path: str) -> str:
    """When a class has already been written and modified, this function
    will read the original script and accordingly change only attributes
    and data model related methods, while preserving custom methods.

    Args:
        rendered_class (str): The newly generated class
        path (str): Path to the previous file
    """

    with open(existing_path, "r") as f:
        existing = f.readlines()

    imports = concatinate_imports(rendered, existing)

    constants = extract_constants(existing)

    # Extract custom methods
    custom_method_positions = get_custom_method_position_slices(existing)
    custom_methods = truncate_custom_methods(existing, custom_method_positions)

    # newly generated code
    rendered_class = remove_imports(rendered)

    # Merge the previous custom methods with the new class
    combined = (
        imports + "\n\n" + constants + "\n\n" + rendered_class + "\n\n" + custom_methods
    )

    return combined


def extract_constants(custom_class: List[str]) -> str:
    """Extracts constants from a custom class. This includes all statements except
    import statements before the class definition

    Args:
        custom_class (List[str]): List of strings representing the generated code

    Returns:
        str: Import statements as a string
    """

    constants = []
    for line in custom_class:
        line = line.strip()

        if line.startswith("@") or line.startswith("class"):
            constants.append("\n")
            return "".join(constants)
        elif line.startswith("from") or line.startswith("import"):
            continue
        else:
            constants.append(line)

    return ""


def concatinate_imports(new_code: List[str], previous_code: List[str]) -> str:
    """_summary_

    Args:
        new_code (List[str]): Code for the new module
        previous_code (List[str]): Code for the previous module

    Returns:
        str: Unique, concatenated import statements
    """

    # Get all imports
    imports = []  # import ...
    from_modules = []  # from ... import ...

    # Get all imports from the new module
    for node in ast.walk(ast.parse(new_code)):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.Import) and ast.unparse(node) not in [
            ast.unparse(imp) for imp in imports
        ]:
            imports.append(node)

        if isinstance(node, ast.Import):
            continue

        if node.module not in [imp.module for imp in from_modules]:
            from_modules.append(node)

    for node in ast.walk(ast.parse("\n".join(previous_code))):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.Import) and ast.unparse(node) not in [
            ast.unparse(imp) for imp in imports
        ]:
            imports.append(node)

        if not isinstance(node, ast.ImportFrom):
            continue

        if node.module not in [from_import.module for from_import in from_modules]:
            from_modules.append(node)

        else:
            # Add classes to existing imports of modules
            for from_import in from_modules:
                if from_import.module != node.module:
                    continue
                for module_class in node.names:
                    if module_class.name not in [
                        submod.name for submod in from_import.names
                    ]:
                        from_import.names.append(module_class)

    all_imports = imports + from_modules

    imports = [ast.unparse(node) for node in all_imports]

    return "\n".join(imports)


def get_custom_method_position_slices(custom: List[str]) -> List[Tuple[int, int]]:
    """Extracts the start and end positions of custom methods in a class

    Args:
        custom (List[str]): List of strings representing the existing code

    Returns:
        List[Tuple[int, int]]: List of tuples representing the start and
        end positions of custom methods of the existing code.
    """

    # Identify lines where functions start
    custom_method_starts = []
    for line_count, line in enumerate(custom):
        if not re.findall(FUNCTION_PATTERN, line):
            continue

        # Ignore sdrdm-generated methods
        if re.findall(ADDER_PATTERN, line):
            continue
        elif re.findall(ANNOTATION_PATTERN, line):
            continue
        elif re.findall(XML_PARSER_PATTERN, line):
            continue

        # Account for decorators
        if custom[line_count - 1].strip().startswith("@"):
            if custom[line_count - 2].strip().startswith("@"):
                custom_method_starts.append(line_count - 2)
            custom_method_starts.append(line_count - 1)
        else:
            custom_method_starts.append(line_count)

    if not custom_method_starts:
        return []

    custom_method_ends = [start - 1 for start in custom_method_starts[1:]]
    custom_method_ends.append(len(custom))

    assert len(custom_method_starts) == len(
        custom_method_ends
    ), "The number of method starts and ends do not match."

    return list(zip(custom_method_starts, custom_method_ends))


def truncate_custom_methods(
    custom: List[str], method_slices: List[Tuple[int, int]]
) -> List[str]:

    if not method_slices:
        return ""

    return "\n".join(
        ["".join(custom[slice(*start_end)]) for start_end in method_slices]
    )


def remove_imports(rendered: List[str]) -> List[str]:
    """Removes all import statements from the rendered code

    Args:
        rendered (List[str]): List of strings representing the rendered code

    Returns:
        List[str]: List of strings representing the rendered code without import statements
    """

    rendered = rendered.split("\n")

    try:
        start = [
            line_id
            for line_id, line in enumerate(rendered)
            if line.strip().startswith("class")
        ][0]
    except IndexError:
        return "\n"

    res = "\n".join(rendered[start:])

    return res


# def extract_custom_methods(existing_path: str) -> List[str]:
#     with open(existing_path, "r") as file:
#         previous_class = file.read().split("\n")

#     # Identify lines where functions start and end
#     method_starts = []
#     for line_count, line in enumerate(previous_class):
#         if not re.findall(FUNCTION_PATTERN, line):
#             continue

#         # Ignore adder, annotation, and xml parser functions
#         if re.findall(ADDER_PATTERN, line):
#             continue
#         elif re.findall(ANNOTATION_PATTERN, line):
#             continue
#         elif re.findall(XML_PARSER_PATTERN, line):
#             continue

#         # Account for decorators
#         if previous_class[line_count - 1].strip().startswith("@"):
#             if previous_class[line_count - 2].strip().startswith("@"):
#                 method_starts.append(line_count - 2)
#             method_starts.append(line_count - 1)
#         else:
#             method_starts.append(line_count)

#     # Deduct the end of each function
#     method_ends = [fun_start - 1 for fun_start in method_starts[1:]]
#     method_ends.append(len(previous_class))

#     # Extract each custom method
#     methods = []
#     for start, end in zip(method_starts, method_ends):
#         methods.append("".join(previous_class[start:end]))

#     return "".join(methods)
