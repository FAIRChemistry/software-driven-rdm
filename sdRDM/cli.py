import typer
import os

from typing import Optional
from sdRDM.generator.codegen import FORMAT_MAPPING, generate_python_api
from sdRDM.generator.schemagen import generate_schema


app = typer.Typer()


@app.command()
def generate(
    path: str = typer.Option(..., help="Path to the data model specifications"),
    out: str = typer.Option(".", help="Destination where the Software will be written"),
    name: str = typer.Option(..., help="Name of the resulting software model"),
    url: Optional[str] = typer.Option(
        None, help="URL to the templates GitHub repository"
    ),
    commit: Optional[str] = typer.Option(
        None, help="Commit hash from which this API was generated"
    ),
):
    """Generates a Python API based on the Markdown fiels found in the path.

    Args:
        path (str, optional): Path to the data model specifications.
        out (str, optional): Destination where the Software will be written.
        name (str, optional): Name of the resulting software model.
    """

    if not all([url, commit]):
        url, commit = None, None

    generate_python_api(path=path, out=out, name=name, commit=commit, url=url)


@app.command()
def link():
    pass


@app.command()
def schema(
    path: str = typer.Option(..., help="Path to the schema definition"),
    out: str = typer.Option(..., help="Directory where the file will be written to."),
):
    """Generate a Mermaid schema from a given Format.

    Args:
        path (str, optional): Path to the schema definition.
        out (str, optional): Directory where the file will be written to.
    """

    # Set up and execute parser
    extension = os.path.basename(path).split(".")[-1]

    if extension not in FORMAT_MAPPING:
        raise TypeError(f"Extension '{extension}' is unknown.")

    # Generate schemata
    format_type = FORMAT_MAPPING[extension]
    generate_schema(open(path, "r"), out, format_type)


if __name__ == "__main__":
    app()
