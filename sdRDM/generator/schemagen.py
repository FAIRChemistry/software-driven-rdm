import os

from copy import deepcopy
from jinja2 import Template
from typing import Dict

from sdRDM.markdown import MarkdownParser
from sdRDM.generator.classrender import combine_types


def generate_mermaid_schema(path: str, libname: str, parser: MarkdownParser) -> None:
    """Generates a mermaid schema for model inspection based on a markdown model"""

    parser = deepcopy(parser)
    template = Template(open("./templates/mermaid_class.jinja2").read())

    list(map(convert_attributes, parser.objs))

    rendered = template.render(
        inherits=parser.inherits,
        compositions=parser.compositions,
        classes=parser.objs,
        enums=parser.enums,
        externals=parser.external_objects,
    )

    path = os.path.join(path, f"{libname.lower().replace(' ', '')}_schema.md")

    with open(path, "w") as f:
        f.write(rendered)


def convert_attributes(object: Dict) -> None:
    """Converts attributes for readable schema generation"""

    for index, attribute in enumerate(object["attributes"]):
        object["attributes"][index]["type"] = (
            combine_types(attribute["type"], attribute["multiple"], attribute["required"])
            .replace("Union[", "")
            .replace("]]", "]")
        )

        object["attributes"][index]["required"] = "*" if attribute["required"] else ""
