import inspect
import git
import glob
import importlib
import os
import random
import sys
import tempfile
import toml
import yaml

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


def build_library_from_git_specs(
    url: str,
    tmpdirname: str,
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
        tmpdirname (str): Path to the temporary directory the specs are cloned to.
        commit (Optional[str], optional): Hash of the commit to fetch from. Defaults to None.
        tag (Optional[str], optional): Tag of the release or branch to fetch from. Defaults to None.
        only_classes (bool): Returns the raw strings rather than the initialized files
    """

    # Import generator to prevent circular import
    from sdRDM.generator.codegen import generate_python_api

    tmpdirname = tempfile.mkdtemp()

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
    link_paths = [
        os.path.join(tmpdirname, "links.yaml"),
        os.path.join(tmpdirname, "links.yml"),
    ]

    if any([os.path.exists(path) for path in link_paths]):
        extension = [
            os.path.basename(path).split(".")[1]
            for path in link_paths
            if os.path.exists(path)
        ][0]

        links = _get_links(tmpdirname, extension)
    else:
        links = {}

    # Generate API to parse the file
    lib_name = f"sdRDM-Library-{str(random.randint(0,30))}"
    api_loc = os.path.join(tmpdirname, lib_name)

    cls_defs = generate_python_api(
        path=schema_loc,
        dirpath=tmpdirname,
        libname=lib_name,
        url=url,
        commit=str(repo.commit()),
        only_classes=only_classes,
        use_formatter=False,
    )

    if only_classes:
        return cls_defs

    return _import_library(api_loc=api_loc, lib_name=lib_name), links


def _import_library(api_loc: str, lib_name: str):
    spec = importlib.util.spec_from_file_location(  # type: ignore
        lib_name, os.path.join(api_loc, "core", "__init__.py")
    )
    lib = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[lib_name] = lib
    spec.loader.exec_module(lib)

    return lib


def _get_links(
    tmpdir: str,
    extension: str,
):
    """
    Retrieves the links from the link manifest and processes them.

    Returns:
        dict: A dictionary containing the processed links, where the keys are the link names and the values are the corresponding functions.
    """

    manifest_path = os.path.join(tmpdir, f"links.{extension}")
    manifest = yaml.safe_load(open(manifest_path))
    module_path = manifest["module"]
    links = manifest["links"]

    assert isinstance(links, list), "Links must be a list of dictionaries."

    link_funs = {}

    for link in links:
        script_path = link["script"]
        module = _import_link_module(tmpdir, module_path, script_path)
        name, root_cls, fun = _process_link(
            link=link,
            module_path=module_path,
            module=module,
            tmpdir=tmpdir,
        )
        link_funs[name] = (root_cls, fun)

    return link_funs


def _import_link_module(
    tmpdir: str,
    module_path: str,
    script_path: str,
):
    spec = importlib.util.spec_from_file_location(  # type: ignore
        script_path.rstrip(".py"),
        os.path.join(tmpdir, module_path, script_path),
    )

    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)

    return module


def _process_link(
    link: Dict,
    module_path: str,
    module,
    tmpdir: str,
):
    """
    Process a link by loading the template, importing the script, and returning a tuple.

    Args:
        link (dict): A dictionary containing information about the link.
        module_path (str): The path to the module.

    Returns:
        tuple: A tuple containing the name, a lambda function, and the function itself.
    """
    name = link["name"]
    template_path = os.path.join(
        tmpdir,
        module_path,
        link["template"],
    )

    fname = link["function"]
    template = toml.load(open(template_path))
    root_cls = template["__model__"]

    fun = getattr(module, fname)

    assert set(inspect.getfullargspec(fun).args) == set(
        ["dataset", "template"]
    ), f"Function for link '{name}' is missing required arguments 'dataset' and 'template'"

    return (
        name,
        root_cls,
        lambda dataset: fun(dataset=dataset, template=template),
    )
