import setuptools
from setuptools import setup

setup(
    name='sdRDM',
    version='0.0.0',
    author='Range, Jan',
    author_email='jan.range@simtech.uni-stuttgart.de',
    license='MIT License',
    packages=setuptools.find_packages(),
    install_requires=[
        'pydantic',
        'deepdish',
        'xmltodict',
        'lxml'
    ],
    extras_require={
        'test': [
            'pytest'
        ]
    },
)
