import glob
import os
import re
import jinja2
import json
import subprocess
import sys

from joblib import Parallel, delayed
from typing import Dict, Optional
from importlib import resources as pkg_resources

from sdRDM.generator.mermaid import MermaidClass
from sdRDM.generator.schemagen import generate_schema, Format
from sdRDM.generator import templates as jinja_templates

FORMAT_MAPPING: Dict[str, Format] = {"md": Format.MARKDOWN}


def generate_python_api(
    path: str,
    out: str,
    name: str,
    url: Optional[str] = None,
    commit: Optional[str] = None,
):

    # Create library directory
    lib_path = os.path.join(out, name)
    core_path = os.path.join(lib_path, "core")
    schema_path = os.path.join(lib_path, "schemes")

    os.makedirs(core_path, exist_ok=True)

    # Add __init__ for module compliance
    init_lib_template = jinja2.Template(
        pkg_resources.read_text(jinja_templates, "init_file_library.jinja2")
    )
    with open(os.path.join(lib_path, "__init__.py"), "w") as f:
        if all([url, commit]):
            f.write(init_lib_template.render(url=url, commit=commit))

    # Read and find all files
    if os.path.isdir(path):
        specifications = list(glob.glob(os.path.join(path, "*")))
        is_single = len(specifications) == 1
    elif os.path.isfile(path):
        specifications = [path]
        is_single = True
    else:
        raise TypeError(f"Given path '{path}' is neither a file nor a directory.")

    for file in specifications:
        extension = os.path.basename(file).split(".")[-1]

        if extension not in FORMAT_MAPPING:
            pass

        # Generate schemata
        format_type = FORMAT_MAPPING[extension]
        mermaid_path, metadata_path = generate_schema(
            open(file, "r"), schema_path, format_type
        )

        # Generate the API
        write_module(
            schema=mermaid_path,
            descriptions_path=metadata_path,
            out=core_path,
            is_single=is_single,
            url=url,
            commit=commit,
        )


def write_module(
    schema: str,
    descriptions_path: str,
    out: str,
    is_single: bool = False,
    commit: Optional[str] = None,
    url: Optional[str] = None,
) -> None:
    """Renders and writes a module based on a Mermaid schema

    Steps:

        1. Extract all class definitions including imports and attributes
        2. Build a dependency tree to traverse later on
        3. Render, write and re-format given classes

    Args:
        schema (str): Path to the Mermaid class diagram
        descriptions (str): Path to the descriptions JSON
        out (str): Path to the target module folder
    """

    # (0) Build target path
    if is_single:
        path = out
    else:
        path = os.path.join(out, os.path.basename(schema).split(".")[0])
    descriptions: Dict = json.loads(open(descriptions_path).read())
    os.makedirs(path, exist_ok=True)

    # (1) Get class definitions
    class_defs = get_class_definitions(schema, descriptions)

    # (2) Build dependency tree
    tree = create_dependency_tree(open(schema).read())

    # (3) Render, write and re-format classes
    write_class(tree=tree, classes=class_defs, dirpath=path, url=url, commit=commit)

    # (3) Finally, write the __init__ file
    init_path = os.path.join(path, "__init__.py")
    with open(init_path, "w") as f:
        module_init = render_dunder_init(
            classes=class_defs, module_doc=descriptions.get("docstring")
        )
        f.write(module_init)

    subprocess.run([sys.executable, "-m", "black", "-q", init_path])


def get_class_definitions(path: str, descriptions) -> Dict[str, MermaidClass]:
    """Retrieves the individual class definitions from a mermaid diagram"""

    cls_string = open(path).read()
    classes = cls_string.split("class ")[1::]

    definitions = {}
    for cls_def in classes:
        cls_def = MermaidClass.parse(cls_def, descriptions)
        definitions[cls_def.name] = cls_def

    return definitions


def create_dependency_tree(mermaid: str):
    """Creates a dependency tree for the data model"""

    # Parse the raw mermaid file to extract all inheritances (<--)
    relation_regex = re.compile(r"([a-zA-Z]*) <-- ([a-zA-Z]*)")
    relations = relation_regex.findall(mermaid)
    results = {}

    while len(relations) > 0:

        # Create a tree from relations
        nodes = {}
        root = next(
            iter(
                set(start for start, _ in relations) - set(end for _, end in relations)
            )
        )
        for start, end in relations:
            nodes.setdefault(start, {})[end] = nodes.setdefault(end, {})

        result = {root: nodes[root]}

        # Get all those classes that have already been found
        # in the first iteration of the tree building
        used_classes = [name for name in get_keys(result)]

        # Remove all those relations that included the root
        relations = list(
            filter(lambda relation: relation[1] not in used_classes, relations)
        )

        results.update(result)

    return results


def get_keys(dictionary):
    """Recursion to traverse through nested dictionaries"""
    keys = []

    for key, item in dictionary.items():
        keys.append(key)
        if item != {}:
            keys += get_keys(item)
    return keys


def write_class(tree: dict, classes: dict, dirpath: str, url, commit, inherit=None):
    """Recursively writes classes"""

    used_classes = _write_dependent_classes(
        tree=tree,
        classes=classes,
        dirpath=dirpath,
        inherit=inherit,
        url=url,
        commit=commit,
    )

    kwargs = {
        "classes": classes,
        "dirpath": dirpath,
        "used_classes": used_classes,
        "url": url,
        "commit": commit,
    }

    Parallel(n_jobs=-1)(
        delayed(_write_lone_class)(cls_obj=cls_obj, **kwargs)
        for cls_obj in classes.values()
    )


def _write_lone_class(cls_obj, classes: dict, dirpath: str, used_classes, url, commit):

    if cls_obj.name in used_classes:
        return

    # First, check if all arbitrary types exist
    # if not render them to a file
    for sub_class in cls_obj.sub_classes:

        try:
            sub_class = classes[sub_class]
        except KeyError:
            raise ValueError(
                f"Cant locate object \033[1m{sub_class}\033[0m in specifications. Please make sure to include this object in your file."
            )

        cls_obj.imports.add(f"from .{sub_class.fname} import {sub_class.name}")

    # Finally, render the given class
    _render_class(cls_obj, dirpath, None, classes=classes, url=url, commit=commit)


def _write_dependent_classes(
    tree: dict,
    classes: dict,
    dirpath: str,
    url: str,
    commit: str,
    inherit=None,
):
    # Write classes from the dependency tree
    used_classes = []
    for cls_name, sub_cls in tree.items():

        # Get the class object
        cls_obj = classes[cls_name]

        # First, check if all arbitrary types exist
        # if not render them to a file
        for sub_class in cls_obj.sub_classes:
            sub_class = classes[sub_class]
            cls_obj.imports.add(f"from .{sub_class.fname} import {sub_class.name}")

            _render_class(
                sub_class,
                dirpath,
                inherit=None,
                classes=classes,
                url=url,
                commit=commit,
            )
            used_classes.append(sub_class.name)

        # Finally, render the given class
        if cls_name not in used_classes:
            _render_class(
                cls_obj,
                dirpath,
                inherit,
                classes=classes,
                url=url,
                commit=commit,
            )
        used_classes.append(cls_name)

        # Repeat process for sub-classes
        if sub_cls:
            used_classes += _write_dependent_classes(
                tree=sub_cls,
                classes=classes,
                dirpath=dirpath,
                inherit=cls_obj,
                url=url,
                commit=commit,
            )

    return used_classes


def _render_class(cls_obj, dirpath, inherit, classes, url, commit):
    """Renders imports, attributes and methods of a class"""

    path = os.path.join(dirpath, cls_obj.fname + ".py")

    # Check if there are any sub classes in the attributes
    # that do not have any required field and thus can be
    # set as a default factory
    _set_optional_classes_as_default_factories(cls_obj, classes)

    with open(path, "w") as file:
        attributes = cls_obj._render_class_attrs(
            inherit=inherit, url=url, commit=commit
        )
        add_methods = cls_obj._render_add_methods(classes=classes)
        imports = cls_obj._render_imports(inherits=inherit)

        if add_methods:
            file.write(f"{imports}\n{attributes}\n{add_methods}")
        else:
            file.write(f"{imports}\n{attributes}")

    # Call black to format everything
    subprocess.run([sys.executable, "-m", "black", "-q", path])


def _set_optional_classes_as_default_factories(cls_obj, classes):
    """Checks if there are any optional classes that can be set as default factory"""

    for name, attribute in cls_obj.attributes.items():
        dtype = re.sub(r"\[|\]|Union|Optional", "", attribute["dtype"])

        if dtype not in classes:
            continue

        # Check if the datatype has only optional values
        is_optional = all(
            bool(re.match(r"List|Optional", attr["dtype"]))
            for attr in classes[dtype].attributes.values()
        )

        if is_optional:
            cls_obj.attributes[name]["default_factory"] = dtype
            del cls_obj.attributes[name]["default"]


def render_dunder_init(classes: dict, module_doc):
    """Renders the __init__ file of the module"""

    # Get the init template
    init_template = jinja2.Template(
        pkg_resources.read_text(jinja_templates, "init_file_template.jinja2")
    )

    return init_template.render(
        classes=sorted(classes.values(), key=lambda cls: cls.fname),
        docstring=module_doc.replace("/", "").replace('"', "'"),
    )
