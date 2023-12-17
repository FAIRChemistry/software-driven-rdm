import pytest


@pytest.mark.e2e
def test_json_deserialisation(model_all, model_all_dataset):
    """Checks whether the parsed JSON file is correctly deserialised"""

    expected = model_all_dataset.to_dict()
    given = model_all.Root.from_json(
        open("tests/fixtures/static/model_all_expected.json")
    ).to_dict()

    assert given == expected, "JSON deserialisation does not match"


@pytest.mark.e2e
def test_yaml_deserialisation(model_all, model_all_dataset):
    """Checks whether the parsed YAML file is correctly deserialised"""

    expected = model_all_dataset.to_dict()
    given = model_all.Root.from_yaml(
        open("tests/fixtures/static/model_all_expected.yaml")
    ).to_dict()

    assert given == expected, "YAML deserialisation does not match"
