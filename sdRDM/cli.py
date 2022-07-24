from typing import Optional
import typer

from sdRDM.generator.codegen import generate_python_api

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

    generate_python_api(path=path, out=out, name=name)


@app.command()
def link():
    pass


if __name__ == "__main__":
    app()
