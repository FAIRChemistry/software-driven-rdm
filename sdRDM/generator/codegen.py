import json
import os
import subprocess
import sys

from glob import glob
from typing import List, Dict, Optional
from sdRDM.generator.utils import extract_modules
from sdRDM.markdown.markdownparser import MarkdownParser
from sdRDM.tools.gitutils import _import_library

from .classrender import render_object
from .enumrender import render_enum
from .initrender import render_core_init_file, render_library_init_file
from .schemagen import generate_mermaid_schema
from .updater import preserve_custom_functions


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

    generate_api_from_parser(
        parser=parser,
        dirpath=dirpath,
        libname=libname,
        url=url,
        commit=commit,
        use_formatter=use_formatter,
    )


def generate_api_from_parser(
    parser: MarkdownParser,
    dirpath: str,
    libname: str,
    url: Optional[str] = None,
    commit: Optional[str] = None,
    use_formatter: bool = True,
):
    # Create directory structure
    libpath = create_directory_structure(dirpath, libname)

    # Write classes to the directory
    write_classes(
        libpath,
        parser.objects,
        parser.enums,
        parser.inherits,
        use_formatter,
        url,
        commit,
    )

    # Write init files
    core_init = render_core_init_file(parser.objects, parser.enums)
    save_rendered_to_file(
        core_init,
        os.path.join(libpath, "core", "__init__.py"),
        use_formatter,
    )

    lib_init = render_library_init_file(parser.objects, parser.enums, url, commit)
    save_rendered_to_file(
        lib_init,
        os.path.join(libpath, "__init__.py"),
        use_formatter,
    )

    # Write schema to library
    generate_mermaid_schema(os.path.join(libpath, "schemes"), libname, parser)
    _write_json_schemes(libpath, libname)


def write_classes(
    libpath: str,
    objects: List[Dict],
    enums: List[Dict],
    inherits: List[Dict],
    use_formatter: bool,
    repo: Optional[str] = None,
    commit: Optional[str] = None,
) -> None:
    """Renders classes that were parsed from a markdown model and creates a library."""

    # Keep track of small types
    small_types = {
        small_type["name"]: small_type
        for object in objects
        for small_type in object["subtypes"]
    }

    for object in objects:
        rendered = render_object(
            object,
            objects,
            enums,
            inherits,
            repo,
            commit,
            small_types,
        )
        path = os.path.join(libpath, "core", f"{object['name'].lower()}.py")
        save_rendered_to_file(rendered, path, use_formatter)

    for enum in enums:
        rendered = render_enum(enum)
        path = os.path.join(libpath, "core", f"{enum['name'].lower()}.py")
        save_rendered_to_file(rendered, path, use_formatter)


def save_rendered_to_file(rendered: str, path: str, use_formatter: bool) -> None:
    """Saves a rendered Object, Enum or Init to a file"""

    if os.path.isfile(path):
        rendered = preserve_custom_functions(rendered, path)

    with open(path, "w") as f:
        f.write(rendered)

    if use_formatter:
        subprocess.run([sys.executable, "-m", "black", "-q", "--preview", path])
        subprocess.run(
            [
                sys.executable,
                "-m",
                "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                path,
            ]
        )


def create_directory_structure(path: str, libname: str) -> str:
    """Creates all necessary directories to which the code will be written"""

    libpath = os.path.join(path, libname)

    os.makedirs(os.path.join(libpath, "core"), exist_ok=True)
    os.makedirs(os.path.join(libpath, "schemes"), exist_ok=True)

    return libpath


def _write_json_schemes(libpath: str, lib_name: str):
    """
    Write JSON schemas for each class in the library.

    Args:
        libpath (str): The path to the library.
        lib_name (str): The name of the library.

    Returns:
        None
    """
    lib = extract_modules(
        _import_library(
            api_loc=libpath,
            lib_name=lib_name,
        ),
        links={},
    )

    for name, cls in lib.get_classes().items():
        dir_path = os.path.join(libpath, "schemes", "json")
        path = os.path.join(dir_path, f"{name}.json")

        os.makedirs(dir_path, exist_ok=True)

        with open(path, "w") as f:
            json.dump(cls.model_json_schema(), f, indent=2)
