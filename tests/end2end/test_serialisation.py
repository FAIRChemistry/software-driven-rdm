import json, yaml


def test_json_serialisation(model_all_dataset):
    """Checks the json serialisation of the model"""

    expected = json.load(open("tests/fixtures/static/model_all_expected.json"))
    given = json.loads(model_all_dataset.json())

    assert given == expected, "JSON serialisation does not match"


def test_yaml_serialisation(model_all_dataset):
    """Checks the yaml serialisation of the model"""

    expected = yaml.safe_load(open("tests/fixtures/static/model_all_expected.yaml"))
    given = yaml.safe_load(model_all_dataset.yaml())

    assert given == expected, "YAML serialisation does not match"
