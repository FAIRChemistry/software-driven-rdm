import os
import re
import yaml
import jinja2
import json
import subprocess
import sys

from typing import Dict
from enum import Enum
from importlib import resources as pkg_resources

from sdRDM.generator import templates as jinja_templates


class DataTypes(Enum):
    """Holds Data Type mappings"""

    string = ("str", None)
    float = ("float", None)
    int = ("int", None)
    posfloat = ("PositiveFloat", "from pydantic.types import PositiveFloat")
    PositiveFloat = ("PositiveFloat", "from pydantic.types import PositiveFloat")
    date = ("date", "from datetime import date")

    @classmethod
    def get_value_list(cls):
        return [member.value[0] for member in cls.__members__.values()]


class MermaidClass:
    def __init__(self, name: str, attributes: dict, docstring=None):
        self.name = name
        self.docstring = docstring
        self.imports = set()
        self.sub_classes = []
        self.adders = {}

        self.attributes = self._process_attributes(attributes)
        self.fname = self.name.lower()
        self.snake_case = self._camel_to_snake(name)

    @staticmethod
    def _camel_to_snake(name):
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def _process_attributes(self, attributes):
        """Processes attributes accordingly"""

        # Map all data types
        attributes = self._map_attribute_dtypes(attributes)

        # Check for list attributes
        for name, attr in attributes.items():

            # Handle factory datatypes
            dtype = attr.get("dtype")
            multiple = attr.get("multiple")
            required = attr.get("required")

            if multiple:
                self.adders[name] = attr.get("dtype")
                attr["dtype"] = f"List[{dtype}]"
                attr["default_factory"] = "list"
                attr["required"] = None
                self.imports.add("from typing import List")
            elif not required:
                attr["dtype"] = f"Optional[{dtype}]"
                attr["default"] = "None"
                self.imports.add("from typing import Optional")

        return attributes

    def _map_attribute_dtypes(self, attributes):
        """Converts attribute data types to Python types"""

        for attr in attributes.values():

            if attr["dtype"] in DataTypes.__members__:
                dtype, dependency = DataTypes[attr["dtype"]].value
                attr["dtype"] = dtype
            else:
                dtype = attr["dtype"]
                self.sub_classes.append(dtype)
                dependency = None

            if dependency is not None:
                # Add possible dependencies
                self.imports.add(dependency)

        return attributes

    def _render_class_attrs(self, inherit=None):
        """Renders the top part including attributes"""

        cls_tm = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "class_template.jinja2")
        )

        # Generate attribute annotations
        attributes = self._render_attributes()

        return cls_tm.render(
            name=self.name,
            inherit=inherit,
            attributes=attributes,
            docstring=self.docstring,
        )

    def _render_attributes(self):
        """Generates Attribute definitions"""

        attributes = []
        attr_tm = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "attribute_template.jinja2")
        )

        for name, attr in self.attributes.items():

            # Make a copy of the attributes when rendering,
            # since we are dropping some items that are
            # necessary for the add_method
            attr = attr.copy()

            # Get required/type/multiple and drop it from metadata
            required = attr.get("required")
            dtype = attr.get("dtype")

            attr.pop("required")
            attr.pop("dtype")
            attr.pop("multiple")

            attributes.append(
                attr_tm.render(
                    name=name,
                    dtype=dtype,
                    required=required,
                    metadata=self._parse_options(attr),
                ).replace("\n    \n", "")
            )

        # Sort by requirement
        attributes = list(
            sorted(attributes, key=lambda attr: "..." in attr, reverse=True)
        )

        return attributes

    @staticmethod
    def _parse_options(options):
        """Takes care that attribute metadata is kept consistent in types.

        For instance, when "default_factory" is given as "list" it should be given as such,
        while on the other hand a "description" is given as a string and thus to
        render valid code, it has to be put in quotation marks.
        """

        type_factory = {
            "default_factory": lambda value: value,
            "default": lambda value: value,
            "description": lambda value: r'"' + value + r'"',
        }

        def check_numeric(value):
            # Checks whether the given value is of special type

            if value.lower() == "none":
                return value

            try:
                int(value)
                float(value)
                return value
            except ValueError:
                return f'"{value}"'

        for name, value in options.items():

            if name in type_factory:
                fun = type_factory[name]
                options[name] = fun(value)
            else:
                options[name] = check_numeric(value)

        return options

    def _render_imports(self, inherits):
        """Renders the import statements"""

        import_template = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "import_template.jinja2")
        )

        if not inherits:
            # If there are no inherits
            # just import sdRDM
            self.imports.add("import sdRDM")
        else:
            # If so, import the packages accordingly
            self.imports.add(f"from .{inherits.fname} import {inherits.name}")

        # Add Field import
        self.imports.add("from pydantic import Field")

        # Sort everything
        package_imps = list(
            filter(lambda imp: imp.startswith("import"), list(self.imports))
        )

        from_imps = list(
            filter(
                lambda imp: (
                    not bool(re.match(r"from \.[a-zA-Z\.]* import [a-zA-Z]*", imp))
                    and imp.startswith("from")
                ),
                list(self.imports),
            )
        )

        local_imps = list(
            filter(
                lambda imp: bool(
                    re.match(r"^from \.[a-zA-Z\.]* import [a-zA-Z]*", imp)
                ),
                list(self.imports),
            )
        )

        return import_template.render(
            package_imports=sorted(package_imps),
            from_imports=sorted(from_imps),
            local_imports=sorted(local_imps),
        )

    def _render_add_methods(self, classes):
        """Renders add methods for all composite elements"""

        methods = []

        add_template = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "add_method_template.jinja2")
        )

        for attribute, add_class in self.adders.items():

            if add_class in DataTypes.get_value_list():
                continue

            # Fetch the target class
            add_class = classes[add_class]

            # Check and add any typing from the
            # foreign class definition
            for imp in list(add_class.imports):
                if "sdRDM" not in imp:
                    self.imports.add(imp)

            # Get all attributes into the appropriate format
            signature = [
                {"name": name, **attr} for name, attr in add_class.attributes.items()
            ]

            signature = sorted(signature, key=lambda x: "Optional" in x["dtype"])

            methods.append(
                add_template.render(
                    snake_case=attribute,
                    signature=signature,
                    attribute=attribute,
                    cls=add_class.name,
                    summary=f"Adds an instance of '{add_class.name}' to the attribute '{attribute}'.",
                ).replace("..", ".")
            )

        if methods:
            return "\n".join(methods)

    def __repr__(self) -> str:
        return yaml.safe_dump({self.name: self.attributes})

    @classmethod
    def parse(cls, mermaid_cls, descriptions):
        """Parses a mermaid class definition"""

        # Get the class name
        name_regex = re.compile(r"([a-zA-Z]*)\s\{")
        name = name_regex.findall(mermaid_cls)[0]

        # Get the attribute metadata
        descriptions = descriptions[name]

        if not name:
            raise ValueError(
                "Mermaid definition might be faulty. ",
                "Please make sure to follow the standard found at ",
                "https://mermaid-js.github.io/mermaid/#/classDiagram",
            )

        # Get all attributes and types
        attrib_regex = re.compile(r"\+([a-zA-Z]*)(\[.*?\])? ([a-zA-Z|\_]*)(\*?)")
        raw_attrs = attrib_regex.findall(mermaid_cls)
        attributes = {}

        for dtype, multiple, attr_name, required in raw_attrs:
            # TODO add special Type mapping
            attr_metadata = descriptions["attributes"][attr_name]
            attr_dict = {"dtype": dtype, **attr_metadata}

            if multiple:
                attr_dict["multiple"] = True
            else:
                attr_dict["multiple"] = False

            if required:
                attr_dict["required"] = True
            else:
                attr_dict["required"] = False

            attributes[attr_name] = attr_dict

        if not attributes:
            raise ValueError(
                "Mermaid definition might be faulty. ",
                "Please make sure to follow the standard found at ",
                "https://mermaid-js.github.io/mermaid/#/classDiagram",
            )

        return cls(
            name=name, attributes=attributes, docstring=descriptions.get("docstring")
        )


def write_module(
    schema: str, descriptions_path: str, out: str, is_single: bool = False
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
    write_class(tree=tree, classes=class_defs, dirpath=path)

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


def write_class(tree: dict, classes: dict, dirpath: str, inherit=None):
    """Recursively writes classes"""

    used_classes = _write_dependent_classes(tree, classes, dirpath, inherit)
    _write_lone_classes(classes, dirpath, None, used_classes)


def _write_lone_classes(classes: dict, dirpath: str, inherit, used_classes):

    for cls_name, cls_obj in classes.items():

        # Guard clause
        if cls_name in used_classes:
            continue

        # First, check if all arbitrary types exist
        # if not render them to a file
        for sub_class in cls_obj.sub_classes:
            sub_class = classes[sub_class]
            cls_obj.imports.add(f"from .{sub_class.fname} import {sub_class.name}")

            if sub_class not in used_classes:
                _render_class(sub_class, dirpath, inherit=None, classes=classes)

        # Finally, render the given class
        _render_class(cls_obj, dirpath, inherit, classes=classes)


def _write_dependent_classes(tree: dict, classes: dict, dirpath: str, inherit=None):
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

            _render_class(sub_class, dirpath, inherit=None, classes=classes)
            used_classes.append(sub_class.name)

        # Finally, render the given class
        if cls_name not in used_classes:
            _render_class(cls_obj, dirpath, inherit, classes=classes)
        used_classes.append(cls_name)

        # Repeat process for sub-classes
        if sub_cls:
            used_classes += _write_dependent_classes(
                tree=sub_cls, classes=classes, dirpath=dirpath, inherit=cls_obj
            )

    return used_classes


def _render_class(cls_obj, dirpath, inherit, classes):
    """Renders imports, attributes and methods of a class"""

    path = os.path.join(dirpath, cls_obj.fname + ".py")

    with open(path, "w") as file:
        attributes = cls_obj._render_class_attrs(inherit=inherit)
        add_methods = cls_obj._render_add_methods(classes=classes)
        imports = cls_obj._render_imports(inherits=inherit)

        if add_methods:
            file.write(f"{imports}\n{attributes}\n{add_methods}")
        else:
            file.write(f"{imports}\n{attributes}")

    # Call black to format everything
    subprocess.run([sys.executable, "-m", "black", "-q", path])


def render_dunder_init(classes: dict, module_doc):
    """Renders the __init__ file of the module"""

    # Get the init template
    init_template = jinja2.Template(
        pkg_resources.read_text(jinja_templates, "init_file_template.jinja2")
    )

    return init_template.render(
        classes=sorted(classes.values(), key=lambda cls: cls.fname),
        docstring=module_doc,
    )
