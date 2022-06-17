import typer
import os
import glob

from sdRDM.generator import write_module, parse_markdown

app = typer.Typer()

type_mapping = {"md": parse_markdown}


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
    for file in glob.glob(os.path.join(path, "*")):
        extension = os.path.basename(file).split(".")[-1]

        if extension not in type_mapping:
            pass

        # Generate schemata
        type_fun = type_mapping[extension]
        mermaid_path, metadata_path = type_fun(file, schema_path)

        # Generate the API
        write_module(schema=mermaid_path, descriptions=metadata_path, out=core_path)


@app.command()
def link():
    pass


if __name__ == "__main__":
    app()
