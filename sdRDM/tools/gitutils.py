import git
import glob
import importlib
import os
import random
import subprocess
import sys
import tempfile
import toml
import yaml

from functools import lru_cache
from typing import Optional, Union, Type, Dict

CACHE_SIZE = 20


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


@lru_cache(maxsize=CACHE_SIZE)
def build_library_from_git_specs(
    url: str,
    commit: Optional[str] = None,
    tag: Optional[str] = None,
    only_classes: bool = False,
) -> Union[Dict, Type]:
    """Fetches a Markdown specification from a git repository and builds the library accordingly.

    This function will clone the repository into a temporary directory and
    builds the correpsonding API and loads it into the memory. After that
    the cloned repository is deleted and the root object(s) detected.

    Args:
        url (str): Link to the git repository. Use the URL ending with ".git".
        commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
        tag (Optional[str], optional): Tag of the release or branch to fetch from. Defaults to None.
        only_classes (bool): Returns the raw strings rather than the initialized files
    """

    # Import generator to prevent circular import
    from sdRDM.generator.codegen import generate_python_api

    with tempfile.TemporaryDirectory() as tmpdirname:

        # Fetch from github
        repo = git.Repo.clone_from(url, tmpdirname)

        # Checkout branches, tags or commit
        if commit:
            repo.git.checkout(commit)
        elif tag:
            repo.git.checkout(tag)

        # Write specification
        schema_loc = os.path.join(tmpdirname, "specifications")

        # Get possible linking templates
        links = {}
        for path in glob.glob(os.path.join(tmpdirname, "links", "*")):

            if path.endswith("toml"):
                linking_template = toml.load(open(path))
            elif path.endswith("yaml") or path.endswith("yml"):
                linking_template = yaml.safe_load(open(path))
            else:
                continue

            # Add to templates
            name = os.path.basename(path).split(".")[0]
            links[name] = linking_template

        # Generate API to parse the file
        lib_name = f"sdRDM-Library-{str(random.randint(0,30))}"
        api_loc = os.path.join(tmpdirname, lib_name)
        cls_defs = generate_python_api(
            path=schema_loc,
            out=tmpdirname,
            name=lib_name,
            url=url,
            commit=str(repo.commit()),
            only_classes=only_classes,
            use_formatter=False,
        )

        if only_classes:
            return cls_defs

        return _import_library(api_loc=api_loc, lib_name=lib_name), links


@lru_cache(maxsize=CACHE_SIZE)
def _import_library(api_loc: str, lib_name: str):
    spec = importlib.util.spec_from_file_location(  # type: ignore
        lib_name, os.path.join(api_loc, "core", "__init__.py")
    )
    lib = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[lib_name] = lib
    spec.loader.exec_module(lib)

    return lib
