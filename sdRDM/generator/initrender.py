from jinja2 import Template
from typing import List, Dict, Optional
from importlib import resources as pkg_resources

from sdRDM.generator import templates as jinja_templates


def render_core_init_file(objects: List[Dict], enums: List[Dict]) -> str:
    """Creates a core __init__ file with all necessary imports and declarations"""

    template = Template(
        pkg_resources.read_text(jinja_templates, "init_file_template.jinja2")
    )

    return template.render(
        classes=[
            {"fname": obj["name"].lower(), "name": obj["name"]}
            for obj in objects + enums
        ]
    )

def render_library_init_file(
    objects: List[Dict],
    enums: List[Dict],
    url: Optional[str] = None,
    hash: Optional[str] = None
) -> str:
    """Creates a library __init__ file with all necessary imports and declarations"""
    
    if url is None:
        url = ""
    if hash is None:
        hash = ""
    
    template = Template(
        pkg_resources.read_text(jinja_templates, "init_file_library.jinja2")
    )
    
    return template.render(
        url=url,
        hash=hash,
        classes=[
            {"fname": obj["name"].lower(), "name": obj["name"]}
            for obj in objects + enums
        ]
    )
    