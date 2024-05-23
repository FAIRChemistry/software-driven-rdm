from typing import Any

from pydantic_core import core_schema


class Identifier:
    """This class is used to identify an entity in sdRDM.

    The main use for this class is to provide ways to identify
    if a given string is an identifier or not.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler,
    ):
        return core_schema.no_info_after_validator_function(
            cls._validate, core_schema.str_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema, handler
    ):
        field_schema = handler(core_schema)
        field_schema.update(type='string', format='identifier')
        return field_schema

    @classmethod
    def _validate(cls, __input_value: str) -> str:
        return __input_value
