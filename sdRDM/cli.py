import typer
import os
import glob

from typing import Dict

from sdRDM.generator import write_module, generate_schema, Format
from sdRDM.generator.abstractparser import SchemaParser

app = typer.Typer()

FORMAT_MAPPING: Dict[str, Format] = {"md": Format.MARKDOWN}


@app.command()
def generate(
    path: str = typer.Option("", help="Path to the data model specifications"),
    out: str = typer.Option("", help="Destination where the Software will be written"),
    name: str = typer.Option("", help="Name of the resulting software model"),
):

    # Create library directory
    lib_path = os.path.join(out, name)
    core_path = os.path.join(lib_path, "core")
    schema_path = os.path.join(lib_path, "schemes")

    os.makedirs(core_path, exist_ok=True)

    # Add __init__ for module compliance
    open(os.path.join(lib_path, "__init__.py"), "w")

    # Read and find all files
    specifications = list(glob.glob(os.path.join(path, "*")))
    is_single = len(specifications) == 1

    for file in specifications:
        extension = os.path.basename(file).split(".")[-1]

        if extension not in FORMAT_MAPPING:
            pass

        # Generate schemata
        format_type = FORMAT_MAPPING[extension]
        mermaid_path, metadata_path = generate_schema(file, schema_path, format_type)

        # Generate the API
        write_module(
            schema=mermaid_path,
            descriptions_path=metadata_path,
            out=core_path,
            is_single=is_single,
        )


@app.command()
def link():
    pass


if __name__ == "__main__":
    app()
