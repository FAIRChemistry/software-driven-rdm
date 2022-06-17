import setuptools
from setuptools import setup

setup(
    name="sdRDM",
    version="0.0.1",
    author="Range, Jan",
    author_email="jan.range@simtech.uni-stuttgart.de",
    license="MIT License",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["softdata=sdRDM.cli:app"]},
    include_package_data=True,
    install_requires=[
        "pydantic",
        "deepdish",
        "xmltodict",
        "lxml",
        "jinja2",
        "markdown",
        "beautifulsoup4",
        "black",
        "typer",
    ],
    extras_require={"test": ["pytest"]},
)
