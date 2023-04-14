import typer
import os

from typing import Optional
from sdRDM.markdown.markdownparser import MarkdownParser
from sdRDM.generator.codegen import generate_python_api
from sdRDM.generator.schemagen import generate_mermaid_schema


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

    if url and url.startswith("git://"):
        # Convert into valid URL
        url = url.replace("git://", "https://", 1)

    generate_python_api(path=path, dirpath=out, libname=name, commit=commit, url=url)


@app.command()
def link():
    pass


@app.command()
def schema(
    path: str = typer.Option(..., help="Path to the schema definition"),
    out: str = typer.Option(".", help="Directory where the file will be written to."),
    name: str = typer.Option(..., help="Name of the schema"),
):
    """Generate a Mermaid schema from a given Format.

    Args:
        path (str, optional): Path to the schema definition.
        out (str, optional): Directory where the file will be written to.
    """
    parser = MarkdownParser.parse(open(path, "r"))
    generate_mermaid_schema(out, name, parser)


if __name__ == "__main__":
    app()
