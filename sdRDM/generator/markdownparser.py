import jinja2
import json
import markdown
import os
import re

from bs4 import BeautifulSoup
from bs4.element import Tag
from importlib import resources as pkg_resources

from sdRDM.generator import templates as jinja_templates
from sdRDM.generator.codegen import DataTypes


def parse_markdown(path: str, out: str):
    """
    Converts a markdown specification file to a Mermaid Class Definition and metadata that
    in turn can be used to generate an API from.

    Args:
        path (str): Path to the Markdown file
        out (str): Destination of the resulting Mermaid and Metadata JSON file
    """

    name, definitions, inherits, soup = extract_classes_from_markdown(path)
    compositions = construct_class_definitions(definitions, soup)
    template = jinja2.Template(
        pkg_resources.read_text(jinja_templates, "mermaid_class.jinja2")
    )
    mermaid_string = template.render(
        inherits=inherits, compositions=compositions, classes=definitions.values()
    )

    # Create dirs if not already created
    os.makedirs(out, exist_ok=True)

    # Set paths for each file
    mermaid_path = os.path.join(out, f"{name}.md")
    metadata_path = os.path.join(out, f"{name}_metadata.json")

    with open(mermaid_path, "w") as file:
        file.write(mermaid_string)

    with open(metadata_path, "w") as file:
        file.write(write_metadata(definitions))

    return mermaid_path, metadata_path


def extract_classes_from_markdown(path: str):
    """Extracts classes from a markdown file using BeautifulSoup"""

    # Convert markdown to HTML
    html = markdown.markdown(open(path).read())
    soup = BeautifulSoup(html, "html.parser")
    module_name = os.path.basename(path).split(".")[0]

    # Bild a list of dependencies
    cls_defs, inherits = {}, []

    # Get all class tags
    tags = soup.find_all("h3")

    for tag in tags:

        content = tag.contents
        definition = {}

        name = content[0].strip(" [")
        definition["name"] = name
        super_class = list(filter(lambda tag: isinstance(tag, Tag), content))

        if super_class:
            definition["super"] = super_class[0].contents[0]
            inherits.append({"parent": definition["super"], "child": name})

        cls_defs[name] = definition

    return module_name, cls_defs, inherits, soup


def construct_class_definitions(definitions, soup):
    """Constructs class definitions based on the HTML that was previously constructed.

    Args:
        definitions (List[Dict]): Contains informations such as name and super classes.

    Returns:
        List[Dict]: Compositions present in the module.
    """

    compositions = []
    for name, definition in definitions.items():
        element = list(
            filter(
                lambda elem: name in repr(elem).split("[")[0] and elem.name == "h3",
                soup,
            )
        )[0]

        for tag in element.next_siblings:
            if tag.name == "h3" and name not in repr(tag.contents).split("["):
                break
            elif tag.name == "p":
                definition["docstring"] = tag.contents[0]
            elif tag.name == "ul":
                definition["attributes"] = _extract_attributes_from_tag(tag)

        # Process compositions
        for attribute in definition["attributes"]:
            if attribute["type"] not in DataTypes.__members__:
                compositions.append(
                    {"module": attribute["type"], "container": definition["name"]}
                )

    return compositions


def _extract_attributes_from_tag(tags: Tag):
    """Extracts attibutes from a <ul> element"""

    attributes = []
    tags = list(filter(lambda elem: r"\n" not in repr(elem), tags))

    for tag in tags:

        if tag.find("strong"):

            if "attribute" in locals():
                attributes.append(attribute)

            attr_pattern = re.compile(r"([a-zA-Z\_]*)(\*?)")
            raw_name = tag.find("strong").contents[0]

            # Get name and required of the attribute
            name, required = attr_pattern.findall(raw_name)[0]
            attribute = {"name": name, "required": required}

        else:
            config, content = tag.contents[0].split(":")
            attribute[config.lower().strip()] = content.strip()

    # Add the last one
    attributes.append(attribute)

    return attributes


def write_metadata(definitions) -> str:
    metadata = definitions.copy()
    for module, item in metadata.items():
        attr_meta = {}
        for attr in item["attributes"]:

            # Build new dictionary w/o mermaid attrs
            attr_name = attr["name"]
            mermaid_keys = [
                "required",
                "type",
                "name",
            ]
            attr_meta[attr_name] = {
                key: item for key, item in attr.items() if key not in mermaid_keys
            }

        metadata[module] = {"attributes": attr_meta, "docstring": item.get("docstring")}

    return json.dumps(metadata, indent=2)


if __name__ == "__main__":
    parse_markdown("specifications/biocatalyst.md", "test")
