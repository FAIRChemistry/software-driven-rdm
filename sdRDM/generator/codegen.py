import os
import subprocess
import sys

from glob import glob
from typing import List, Dict, Optional
from sdRDM.markdown.markdownparser import MarkdownParser

from .classrender import render_object
from .enumrender import render_enum
from .initrender import render_core_init_file, render_library_init_file
from .schemagen import generate_mermaid_schema


def generate_python_api(
    path: str,
    dirpath: str,
    libname: str,
    url: Optional[str] = None,
    commit: Optional[str] = None,
    only_classes: bool = False,
    use_formatter: bool = True,
) -> Optional[MarkdownParser]:
    """Generates a Python API based on a markdown model, which is parsed
    and code generated based on the specifications.

    Args:
        path (str): Path to the markdown model.
        dirpath (str): Directory to which the library will be written
        libname (str): Name of the libary which will be used as directory name.
    """

    # Check if there are multiple models
    if os.path.isdir(path):
        parser = MarkdownParser()
        for file in glob(os.path.join(path, "*.md")):
            parser.add_model(MarkdownParser.parse(open(file)))
    else:
        parser = MarkdownParser.parse(open(path))

    if only_classes:
        return parser

    # Create directory structure
    libpath = create_directory_structure(dirpath, libname)

    # Write classes to the directory
    write_classes(libpath, parser.objs, parser.enums, parser.inherits, use_formatter)

    # Write init files
    core_init = render_core_init_file(parser.objs, parser.enums)
    save_rendered_to_file(core_init, os.path.join(libpath, "core", "__init__.py"))

    lib_init = render_library_init_file(parser.objs, parser.enums, url, commit)
    save_rendered_to_file(lib_init, os.path.join(libpath, "__init__.py"))

    # Write schema to library
    generate_mermaid_schema(os.path.join(libpath, "schemes"), libname, parser)


def write_classes(
    libpath: str,
    objects: List[Dict],
    enums: List[Dict],
    inherits: List[Dict],
    use_formatter: bool,
) -> None:
    """Renders classes that were parsed from a markdown model and creates a library."""

    for object in objects:
        rendered = render_object(object, objects, enums, inherits)
        path = os.path.join(libpath, "core", f"{object['name'].lower()}.py")
        save_rendered_to_file(rendered, path, use_formatter)

    for enum in enums:
        rendered = render_enum(enum)
        path = os.path.join(libpath, "core", f"{enum['name'].lower()}.py")
        save_rendered_to_file(rendered, path, use_formatter)


def save_rendered_to_file(rendered: str, path: str, use_formatter: bool = True) -> None:
    """Saves a rendered Object, Enum or Init to a file"""

    with open(path, "w") as f:
        f.write(rendered)

    if use_formatter:
        subprocess.run([sys.executable, "-m", "black", "-q", "--preview", path])


def create_directory_structure(path: str, libname: str) -> str:
    """Creates all necessary directories to which the code will be written"""

    libpath = os.path.join(path, libname)

    os.makedirs(os.path.join(libpath, "core"), exist_ok=True)
    os.makedirs(os.path.join(libpath, "schemes"), exist_ok=True)

    return libpath
