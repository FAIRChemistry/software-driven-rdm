from typing import List
import jinja2

from importlib import resources as pkg_resources
from typing import List

from sdRDM.generator import templates as jinja_templates


class MermaidEnum:
    def __init__(self, name: str, values: List):
        self.name = name
        self.fname = name.lower()
        self.values = [value.strip() for value in values]

    def render(self):
        add_template = jinja2.Template(
            pkg_resources.read_text(jinja_templates, "enum_template.jinja2")
        )

        return add_template.render(name=self.name, mappings=self.values)
