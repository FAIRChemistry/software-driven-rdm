from datetime import date, datetime
from pydantic import PositiveFloat, PositiveInt, AnyHttpUrl, EmailStr
from typing import List, Union, Optional


def test_scheme(model_all):
    """Tests whether the schemes of a given model are matching with what has been parsed"""

    # Check whether classes are present
    assert hasattr(model_all, "Root"), "Root object not found"
    assert hasattr(model_all, "Nested"), "Nested object not found"

    # Check if the schemes of the classes are correct
    NoneType = type(None)
    SomeEnum = model_all.enums.SomeEnum
    Nested = model_all.Nested

    expected_scheme = [
        ("id", Optional[str]),
        ("str_value", Union[str, NoneType]),
        ("float_value", Union[float, NoneType]),
        ("int_value", Union[int, NoneType]),
        ("bool_value", Union[bool, NoneType]),
        ("date_value", Union[date, NoneType]),
        ("datetime_value", Union[datetime, NoneType]),
        ("posfloat_value", Union[PositiveFloat, NoneType]),
        ("posint_value", Union[PositiveInt, NoneType]),
        ("http_url_value", Union[AnyHttpUrl, NoneType]),
        ("email_value", Union[EmailStr, NoneType]),
        ("bytes_value", Union[bytes, NoneType]),
        ("multiple_primitives", List[float]),
        ("enum_value", Union[SomeEnum, NoneType]),
        ("nested_single_obj", Union[Nested, NoneType]),
        ("nested_multiple_obj", List[Nested]),
        ("referenced_value", Union[Nested, str, NoneType]),
    ]

    given_scheme = [
        (name, field.annotation) for name, field in model_all.Root.model_fields.items()
    ]

    expected_scheme.sort(key=lambda x: x[0])
    given_scheme.sort(key=lambda x: x[0])

    assert len(expected_scheme) == len(
        given_scheme
    ), f"Number of fields does not match - expected: {len(expected_scheme)}, given: {len(given_scheme)}"

    for (given_name, given_type), (expec_name, expec_type) in zip(
        given_scheme, expected_scheme
    ):
        assert (
            given_name == expec_name
        ), f"Names do not match: {given_name} != {expec_name}"
        assert (
            given_type == expec_type
        ), f"Types do not match: {given_type} != {expec_type}"
