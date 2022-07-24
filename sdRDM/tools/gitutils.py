import importlib
import inspect
import os
import subprocess
import sys
import tempfile
import uuid

from functools import lru_cache
from typing import Callable, Optional

from sdRDM.generator.codegen import generate_python_api


class ObjectNode:
    """Helper class used to determine root node(s)."""

    def __init__(self, cls):
        self.name = cls.__name__
        self.parent = None
        self.cls = cls
        self.parent_classes = []

    def add_parent_class(self, sub_class):
        self.parent_classes.append(sub_class)

    def __repr__(self) -> str:
        return repr(self.cls)


@lru_cache(maxsize=5)
def build_library_from_git_specs(url: str, commit: Optional[str] = None):
    """Fetches a Markdown specification from a git repository and builds the library accordingly.

    This function will clone the repository into a temporary directory and
    builds the correpsonding API and loads it into the memory. After that
    the cloned repository is deleted and the root object(s) detected.

    Args:
        url (str): Link to the git repository. Use the URL ending with ".git".
        commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
    """

    with tempfile.TemporaryDirectory() as tmpdirname:

        # Fetch from github
        _fetch_from_git(url=url, path=tmpdirname, cwd=os.getcwd(), commit=commit)

        # Write specification
        schema_loc = os.path.join(tmpdirname, "specifications")

        # Generate API to parse the file
        lib_name = f"sdRDM-Library-{str(uuid.uuid4())}"
        api_loc = os.path.join(tmpdirname, lib_name)
        generate_python_api(
            path=schema_loc, out=tmpdirname, name=lib_name, url=url, commit=commit
        )

        return _import_library(api_loc=api_loc, lib_name=lib_name)


def _fetch_from_git(url: str, path: str, cwd: str, commit: Optional[str] = None):
    """Calls git in the backend and clones the repository"""

    subprocess.call(["git", "clone", url, path])

    if commit:
        os.chdir(path)
        subprocess.call(["git", "config", "--global", "advice.detachedHead", "false"])
        subprocess.call(["git", "checkout", commit])
        os.chdir(cwd)


@lru_cache(maxsize=5)
def _import_library(api_loc: str, lib_name: str):
    spec = importlib.util.spec_from_file_location(  # type: ignore
        lib_name, os.path.join(api_loc, "core", "__init__.py")
    )
    lib = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[lib_name] = lib
    spec.loader.exec_module(lib)

    return lib
