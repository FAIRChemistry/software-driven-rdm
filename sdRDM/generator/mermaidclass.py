from audioop import mul
import re
import jinja2

from enum import Enum
from importlib import resources as pkg_resources
from typing import Dict, List, Optional

from sdRDM.generator import templates as jinja_templates
from sdRDM.generator.mermaidenum import MermaidEnum
from sdRDM.generator.datatypes import DataTypes
from sdRDM.tools.utils import check_numeric

DTYPE_PATTERN = r"List\[|Optional\[|\]"
BUILTINS = ["str", "float", "int", "datetime", "none", "bool", "bytes"]


class MermaidClass:
    def __init__(self, name: str, attributes: dict, docstring: Optional[str] = None):
        self.name = name
        self.docstring = docstring
        self.imports = set()
        self.sub_classes = []
        self.references = []
        self.adders = {}
        self.inherit = None

        self.attributes = self._process_attributes(attributes)
        self.fname = self.name.lower()
        self.snake_case = self._camel_to_snake(name)

        # Process docstring to not include quotation marks
        if isinstance(self.docstring, str):
            self.docstring = self.docstring.replace('"', "")

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

            if self.name.lower() == dtype.lower():
                # Address self-referencing objects
                dtype = dtype.replace(self.name, f"'{self.name}'")

            if "Union" in dtype:
                self.imports.add("from typing import Union")

            if multiple:
                if "Union" not in dtype:
                    self.adders[name] = attr.get("dtype")

                attr["dtype"] = f"List[{dtype}]"
                attr["default_factory"] = "ListPlus"
                attr["required"] = None

                self.imports.add("from typing import List")

            elif not required:
                if "Union" in dtype:
                    raw_types = dtype.replace("Union[", "").replace("]", "").split(",")
                    dtype = ", ".join([type.strip() for type in raw_types])
                    attr["dtype"] = f"Union[{dtype}, None]"
                else:
                    attr["dtype"] = f"Optional[{dtype}]"

                attr["default"] = "None"

                self.imports.add("from typing import Optional")

        return attributes

    def _map_attribute_dtypes(self, attributes):
        """Converts attribute data types to Python types"""

        for name, attr in attributes.items():

            dtypes = attr["dtype"].replace("Union[", "").replace("]", "")

            for dtype in dtypes.split(","):

                if dtype in DataTypes.__members__:
                    dtype, dependencies = DataTypes[dtype].value

                    if "Union" not in attr["dtype"]:
                        # Make sure that native types are added
                        # only when there are no Unions present
                        attr["dtype"] = dtype
                    else:
                        # Make sure that 'string' is converted to 'str'
                        attr["dtype"] = attr["dtype"].replace("string", "str")

                elif dtype.startswith("@"):
                    # Process given references in the format '@[object].[attribute]'
                    reference = dtype.replace("@", "").split(".")

                    if len(reference) == 1:
                        # ID is the default value to fetch from the reference
                        reference.append("id")

                    self.references.append(
                        {
                            "object": reference[0],
                            "target": reference[-1],
                            "attribute": name,
                        }
                    )

                    # Add the object as a dependencies
                    # dependencies = f"from .{reference[0].lower()} import {reference[0]}"
                    dependencies = None

                    # Set the dtype and import Union
                    attr["dtype"] = f"Union[str, '{reference[0]}']"

                    self.imports.add("from typing import Union")
                    self.imports.add("from pydantic import validator")

                else:
                    self.sub_classes.append(dtype)
                    dependencies = None

                if dependencies is not None:
                    # Add possible dependencies
                    self.imports.update(dependencies)

        return attributes

    def _render_class_attrs(self, inherit=None, url=None, commit=None):
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
            url=url,
            commit=commit,
        )

    def _render_attributes(self):
        """Generates Attribute definitions"""

        attributes = []
        attr_tm = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "attribute_template.jinja2")
        )

        for name, attr in self.attributes.items():
            if name == "id":
                continue

            # Make a copy of the attributes when rendering,
            # since we are dropping some items that are
            # necessary for the add_method
            attr = attr.copy()

            # Get required/type/multiple and drop it from metadata
            required = attr.get("required")
            dtype = attr.get("dtype")

            if dtype == self.name:
                dtype = f"'{dtype}'"

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
            "description": lambda value: r'"' + value.replace('"', "'") + r'"',
        }

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
                lambda imp: bool(re.match(r"^from \.[a-zA-Z\.]* import [a-zA-Z]*", imp))
                and f"from .{self.name.lower()} import {self.name}" != imp,
                list(self.imports),
            )
        )

        return import_template.render(
            package_imports=sorted(package_imps),
            from_imports=sorted(from_imps),
            local_imports=sorted(local_imps),
        )

    def _render_add_methods(self, classes):
        """Renders add methods for all ßü´ä´e elements"""

        add_template = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "add_method_template.jinja2")
        )

        methods = []
        adders = list(self.adders.items())

        for attribute, add_class in adders:

            if add_class in DataTypes.get_value_list():
                continue

            # Fetch the target class
            add_class = classes[add_class]

            if isinstance(add_class, MermaidEnum):
                continue

            # Check and add any typing from the
            # foreign class definition
            for imp in list(add_class.imports):
                if "sdRDM" not in imp:
                    self.imports.add(imp)

            # Combine attributes from adder class
            # and their parent class, if given
            add_class_attrs = add_class.attributes
            if add_class.inherit:
                add_class_attrs = {**add_class.inherit.attributes, **add_class_attrs}

            # Add all dependencies
            self._process_adder_dependencies(add_class_attrs=add_class_attrs)

            # Get all attributes into the appropriate format
            signature = [
                {"name": name, **attr} for name, attr in add_class_attrs.items()
                if name != "id"
            ]

            signature = sorted(
                signature,
                key=lambda x: "default" in x
                or repr(x["multiple"]) == "True",  # TODO FIX THIS BETTER
            )

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

    def _process_adder_dependencies(self, add_class_attrs: Dict):
        """Processes the given datatypes found in the adder classes
        to build an add function. This method will add the required
        imports to guarantee the Typing.

        """
        for attr in add_class_attrs.values():
            # Add dependcies from add method
            dtype = re.sub(DTYPE_PATTERN, "", attr["dtype"])

            if dtype in BUILTINS:
                continue

            dtypes = dtype.replace("Union[", "").replace("]", "")
            for dtype in dtypes.split(","):
                dtype = dtype.strip()

                if (
                    dtype.lower() in BUILTINS
                    or dtype.startswith("'")
                    or dtype.lower() in DataTypes.__members__
                ):
                    # Discard builtins and self-references
                    continue

                # Adress Union import and split them up
                # to individually import the classes
                self.imports.add(f"from .{dtype.lower()} import {dtype}")

    def _render_reference_validators(self):
        """Renders all given references as validators"""

        reference_template = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "reference_template.jinja2")
        )

        return "\n".join([reference_template.render(**ref) for ref in self.references])

    @classmethod
    def parse(cls, mermaid_cls, module_meta):
        """Parses a mermaid class definition"""

        # Get the class name
        name_regex = re.compile(r"([a-zA-Z]*)\s\{")
        name = name_regex.findall(mermaid_cls)[0]

        # Get the attribute metadata
        descriptions = module_meta[name]
        objects = (
            list(module_meta.keys())
            + list(module_meta["enums"])
            + list(module_meta["external"])
        )

        if not name:
            raise ValueError(
                "Mermaid definition might be faulty. ",
                "Please make sure to follow the standard found at ",
                "https://mermaid-js.github.io/mermaid/#/classDiagram",
            )

        # Get all attributes and types
        attrib_regex = re.compile(
            r"\+([a-zA-Z0-9\[\]\,\@\.]*)(\[.*?\])? ([a-zA-Z0-9|\_]*)(\*?)"
        )
        raw_attrs = attrib_regex.findall(mermaid_cls)

        attributes = {}

        for dtype, multiple, attr_name, required in raw_attrs:
            # TODO add special Type mapping
            attr_metadata = descriptions["attributes"][attr_name]

            cls._process_attr_metadata(attr_metadata, objects)

            attr_dict = {
                "dtype": dtype,
                "multiple": bool(multiple),
                "required": bool(required),
                **attr_metadata,
            }

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

    @staticmethod
    def _process_attr_metadata(attr_metadata: Dict, objects: List[str]):
        """Helper function used to include specialized processes to options"""
        for name, value in attr_metadata.items():
            if name.lower() == "default":
                if isinstance(value, str) and any(obj in value for obj in objects):
                    attr_metadata[name] = value
                else:
                    attr_metadata[name] = check_numeric(value)
