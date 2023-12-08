import typer
import os

from enum import Enum
from typing import List, Optional
import validators

from sdRDM.base.datamodel import DataModel
from sdRDM.markdown.markdownparser import MarkdownParser
from sdRDM.generator.codegen import generate_python_api
from sdRDM.generator.schemagen import generate_mermaid_schema


class Dialects(Enum):
    xml = lambda model: model.from_xml
    json = lambda model: model.from_json
    yaml = lambda model: model.from_yaml
    hdf5 = lambda model: model.from_hdf5
    h5 = lambda model: model.from_hdf5


app = typer.Typer()


@app.command()
def generate(
    path: str = typer.Option(
        ...,
        help="Path to the data model specifications",
    ),
    out: str = typer.Option(
        ".",
        help="Destination where the Software will be written",
    ),
    name: str = typer.Option(
        ...,
        help="Name of the resulting software model",
    ),
    url: Optional[str] = typer.Option(
        None,
        help="URL to the templates GitHub repository",
    ),
    commit: Optional[str] = typer.Option(
        None,
        help="Commit hash from which this API was generated",
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


@app.command()
def validate(
    files: List[str] = typer.Argument(
        ...,
        help="Path(s) to the file(s) to validate.",
    ),
    schema_loc: str = typer.Option(
        ...,
        help="Path/URL to the schema definition",
    ),
    object: str = typer.Option(
        ...,
        help="Name of the target object within the schema to validate against. If given in the document, this argument is ignored.",
    ),
    format: Optional[Dialects] = typer.Option(
        default=None,
        help="Format of the file to validate. If not given, the format will be inferred from the file extension.",
    ),
):
    """Validates a given file against a schema.

    Args:
        files (List[str]): Path(s) to the file(s) to validate.
        schema_loc (str): Path/URL to the schema definition.
        object (str): Name of the target object within the schema to validate against. If given in the document, this argument is ignored.
        format (Optional[Dialects]): Format of the file to validate. If not given, the format will be inferred from the file extension.
    """

    if validators.url(schema_loc):
        assert schema_loc.endswith(".git"), "Remote GitHub URL must end with .git"
        lib = DataModel.from_git(schema_loc)
    else:
        assert os.path.exists(schema_loc), f"File {schema_loc} does not exist."
        lib = DataModel.from_markdown(schema_loc)

    assert hasattr(lib, object), f"Object {object} not found in schema."

    # Fetch the model from the library
    model = getattr(lib, object)

    for file in files:
        _validate_single_file(file, model, format)


def _validate_single_file(
    file: str,
    model: DataModel,
    format: Optional[Dialects] = None,
):
    """Validates a single file against a schema"""

    assert os.path.exists(file), f"File {file} does not exist."

    if format is None:
        parse_fun = _infer_extension(file)
    else:
        parse_fun = format.value

    try:
        parse_fun(model)(open(file))
        print(f"🎉 File '{file}' is valid.")
    except Exception as e:
        print(f"❌ File {file} is not valid.")
        raise e


def _infer_extension(file: str) -> str:
    """Infers the extension of a file"""
    _, ext = os.path.splitext(file)
    ext = ext.lower().lstrip(".")

    try:
        return getattr(Dialects, ext)
    except AttributeError:
        available = ", ".join(
            [attr for attr in Dialects.__dict__.keys() if not attr.startswith("_")]
        )
        raise ValueError(
            f"Extension '{ext}' not supported or unknown. Please specify one of '{available}'"
        )


if __name__ == "__main__":
    app()
