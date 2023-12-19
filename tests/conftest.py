from datetime import date, datetime
import pytest
import json

from sdRDM.base.datamodel import DataModel
from tests.fixtures.code.enumutils import (
    _empty_mapping_enum_tokens,
    _correct_enum_tokens,
    _incorrect_mapping_enum_tokens,
)
from tests.fixtures.code.objectutils import (
    _correct_option,
    _invalid_option,
    _multiple_option,
    _type_option,
)


@pytest.fixture
def model_all():
    """Loads the data model that contains all supported types (WIP)"""
    return DataModel.from_markdown("tests/fixtures/static/model_all.md")


@pytest.fixture
def model_all_expected():
    """Loads the a dataset that contains all supported types to check tests"""
    return json.load(open("tests/fixtures/static/model_all_expected.json"))


@pytest.fixture
def model_all_dataset(model_all):
    # Create a dataset with the given library
    nested = model_all.Nested(
        id="id",
        str_value="string",
        float_value=1.5,
        int_value=1,
    )

    dataset = model_all.Root(
        id="id",
        str_value="string",
        float_value=1.5,
        int_value=1,
        bool_value=True,
        date_value=date(2023, 12, 17),
        datetime_value=datetime(2023, 12, 17, 15, 55, 44, 245441),
        posfloat_value=1.5,
        posint_value=2,
        http_url_value="https://www.google.com",
        email_value="max.mustermann@muster.de",
        bytes_value="this_is_bytes".encode(),
        multiple_primitives=[1.5, 1.7, 1.9],
        enum_value=model_all.enums.SomeEnum.VALUE1,
        nested_single_obj=nested,
        nested_multiple_obj=[nested],
        referenced_value=nested,
    )

    return dataset


## Enumutils fixtures
@pytest.fixture
def correct_enum_tokens():
    return _correct_enum_tokens()


@pytest.fixture
def incorrect_mapping_enum_tokens():
    return _incorrect_mapping_enum_tokens()


@pytest.fixture
def empty_mapping_enum_tokens():
    return _empty_mapping_enum_tokens()


## Objectutils fixtures
@pytest.fixture
def correct_option():
    return _correct_option()


@pytest.fixture
def invalid_option():
    return _invalid_option()


@pytest.fixture
def type_option():
    return _type_option()


@pytest.fixture
def multiple_option():
    return _multiple_option()
