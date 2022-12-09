import re

from datetime import date, datetime
from typing import Any, get_origin, Dict, List, Optional
from inspect import Signature, Parameter
from pydantic import Field, create_model
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    String,
    Boolean,
    BigInteger,
    ForeignKey,
)
from sdRDM.base.importemodules import ImportedModules

SQL_DATATYPES = {
    str: String,
    int: Integer,
    float: Float,
    bool: Boolean,
    datetime: Date,
    date: Date,
}


class IDGenerator:
    def __init__(self, pattern: str):
        self.pattern = pattern.replace(r"\d", "INDEX")
        self.index = 0
        self.__name__ = "IDGenerator"

    def __call__(self):
        return self.generate_id()

    def generate_id(self):
        id = re.sub(r"\[?INDEX\]?[+|*|?]?", str(self.index), self.pattern)
        self.index += 1
        return id


def generate_model(
    data: Dict,
    name: str,
    base,
    attr_replace: str,
    objs: Dict = {},
    is_root: bool = True,
):
    """Generates a model based on a given file without an existing schema.

    Caution, these models can impose to be incomplete if the data given
    only covers a fraction of the actual schema it was generated from.
    This methods intent is to provide sdRDM's functionalities for parsing
    data on the fly.

    """

    fields = {}
    for field, content in data.items():

        field_params = {}
        if (
            isinstance(content, list)
            and content != []
            and all(isinstance(entry, dict) for entry in content)
        ):
            field_params["default_factory"] = list
            dtype = List[
                generate_model(
                    data=content[0],
                    name=field.capitalize(),
                    base=base,
                    objs=objs,
                    is_root=False,
                    attr_replace=attr_replace,
                )  # type: ignore
            ]
        elif isinstance(content, dict):
            dtype = generate_model(
                data=content,
                name=field.capitalize(),
                base=base,
                objs=objs,
                is_root=False,
                attr_replace=attr_replace,
            )  # type: ignore
        elif isinstance(content, list):
            field_params["default_factory"] = list
            dtype = List[Any]
        else:
            field_params["default"] = None
            dtype = Optional[Any]

        # Perform attribute replacement
        new_name = re.sub(attr_replace, "", field)
        new_name = new_name.replace("-", "_")

        if new_name != field:
            field_params["alias"] = field
            field = new_name

        fields[field] = (dtype, Field(**field_params))

    # Finally create the corresponding object
    objs[name] = create_model(name, __base__=base, **fields)

    if is_root:
        return ImportedModules(classes=objs)
    else:
        return objs[name]


def forge_signature(cls):
    """Changes the signature of a class to include forbidden names such as 'yield'.

    Since PyDantic aliases are also applied to the signature, forbidden names
    such as 'yield' are impossible. This decorator will turn add an underscore
    while the exports aligns to the alias.

    """

    parameters = _construct_signature(cls)
    cls.__signature__ = Signature(parameters=parameters)

    return cls


def _construct_signature(cls):
    """Helper function to extract parameters"""

    parameters = []

    for name, parameter in cls.__signature__.parameters.items():

        if f"{name}_" in cls.__fields__:
            name = f"{name}_"

        parameters.append(
            Parameter(
                name=name,
                kind=parameter.kind,
                default=parameter.default,
                annotation=parameter.annotation,
            )
        )

    return parameters


def object_to_orm(obj, base, foreign_key=None, backref=None, tablename=None):
    """Converts a Pydantic object to an SQL table"""

    tablename = tablename if tablename is not None else obj.__name__
    attributes = {
        "__tablename__": tablename,
        "object_id": Column(
            BigInteger().with_variant(Integer, "sqlite"), primary_key=True
        ),
    }

    if foreign_key is None:
        # If no foreign key is given, pass the current tablename
        # reference to the object_id attribute
        foreign_key = f"{tablename}.object_id"
    else:
        # If a foreign key is given, integrate this one into the ORM
        # This in general applies to one-to-many relationships
        attributes[foreign_key.split(".")[0]] = Column(Integer, ForeignKey(foreign_key))

    if backref:
        # If a backref is given, then there is a one-to-one relations
        # which includes a back-population from both tables
        attributes[backref.lower()] = relationship(backref, back_populates=tablename)

    for name, field in obj.__fields__.items():
        inner_dtype = field.type_
        outer_dtype = field.outer_type_
        is_list = get_origin(outer_dtype) == list

        if hasattr(inner_dtype, "__fields__"):

            if is_list:
                # If its a list it is considered a one to many relationship
                # and thus the FK is put on the sub objects table
                attributes[name] = relationship(field.type_.__name__, lazy=True)
                object_to_orm(
                    obj=field.type_, base=base, foreign_key=foreign_key, tablename=name
                )
            else:
                # If it is just a single sub-object we can reference
                # the FK in this table
                attributes[f"{name}_id"] = Column(
                    Integer, ForeignKey(f"{name.lower()}.object_id")
                )
                attributes[name] = relationship(
                    field.type_.__name__,
                    lazy=True,
                    back_populates=tablename,
                    uselist=False,
                )

                object_to_orm(
                    obj=field.type_, base=base, backref=tablename, tablename=name
                )

        else:
            if is_list:
                attributes[name] = relationship(name, lazy=True)
                attributes[foreign_key.split(".")[0]] = Column(
                    Integer, ForeignKey(foreign_key)
                )
                type(
                    name,
                    (base,),
                    {
                        "__tablename__": name,
                        "object_id": Column(
                            BigInteger().with_variant(Integer, "sqlite"),
                            primary_key=True,
                        ),
                        tablename: Column(
                            Integer, ForeignKey(f"{tablename}.object_id")
                        ),
                        name: Column(
                            SQL_DATATYPES[inner_dtype],
                            nullable=False if field.required else True,
                        ),
                    },
                )
            else:
                attributes[name] = Column(
                    SQL_DATATYPES[inner_dtype],
                    nullable=False if field.required else True,
                )

    # Add the table as a new type
    type(tablename, (base,), attributes)
