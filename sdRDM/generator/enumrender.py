from jinja2 import Template
from typing import Dict
from importlib import resources as pkg_resources

from sdRDM.generator import templates as jinja_templates


def render_enum(enum: Dict) -> str:
    """Renders a given Enum description using a Jinja template"""

    template = Template(
        pkg_resources.read_text(jinja_templates, "enum_template.jinja2")
    )

    assert len(enum["mappings"]) > 0, f"No mappings in Enum {enum['name']}"

    return template.render(name=enum["name"], mappings=enum["mappings"])
