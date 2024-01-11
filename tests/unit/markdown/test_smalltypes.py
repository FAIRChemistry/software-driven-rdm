import pytest

from sdRDM.markdown.smalltypes import (
    _extract_attributes,
    _validate_attribute,
    process_small_type,
)


class Test_ValidateAttribute:
    # Ensure that the function does not raise any exceptions when given valid inputs.
    @pytest.mark.unit
    def test_valid_inputs(self):
        attribute = "name:str"
        attr_name = "person"
        name, dtype = attribute.split(":")
        try:
            _validate_attribute(attribute, attr_name, name, dtype)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    # Ensure that the function correctly validates an attribute with a valid name and data type.
    @pytest.mark.unit
    def test_valid_name_and_dtype(self):
        attribute = "name:str"
        attr_name = "person"
        name, dtype = attribute.split(":")
        try:
            _validate_attribute(attribute, attr_name, name, dtype)
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    # Ensure that the function correctly validates an attribute with a valid name and data type, even when there is whitespace around the name and data type.
    @pytest.mark.unit
    def test_whitespace_name_and_dtype(self):
        attribute = "  name  :  str  "
        attr_name = "person"
        name, dtype = attribute.split(":")
        try:
            _validate_attribute(attribute, attr_name, name.strip(), dtype.strip())
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    # Ensure that the function raises an AssertionError when given an attribute with no name.
    @pytest.mark.unit
    def test_no_name(self):
        attribute = ":str"
        attr_name = "person"
        name, dtype = attribute.split(":")
        with pytest.raises(AssertionError):
            _validate_attribute(attribute, attr_name, name, dtype)

    # Ensure that the function raises an AssertionError when given an attribute with no data type.
    @pytest.mark.unit
    def test_no_dtype(self):
        attribute = "name:"
        attr_name = "person"
        name, dtype = attribute.split(":")
        with pytest.raises(AssertionError):
            _validate_attribute(attribute, attr_name, name, dtype)

    # Ensure that the function raises a ValueError when given an attribute with an invalid data type.
    @pytest.mark.unit
    def test_invalid_dtype(self):
        attribute = "name:invalid"
        attr_name = "person"
        name, dtype = attribute.split(":")
        with pytest.raises(ValueError):
            _validate_attribute(attribute, attr_name, name, dtype)


class Test_ExtractAttributes:
    # Extracts all attributes from a valid small type string
    @pytest.mark.unit
    def test_extract_valid_small_type(self):
        dtypes = "{name: str, age: int, height: float}"
        attr_name = "attribute"
        expected_result = [
            {"name": "name", "type": ["str"], "required": False},
            {"name": "age", "type": ["int"], "required": False},
            {"name": "height", "type": ["float"], "required": False},
        ]

        result = _extract_attributes(dtypes, attr_name)

        assert result == expected_result

    # Returns a list of dictionaries with attribute name, type and required fields
    @pytest.mark.unit
    def test_return_list_of_dictionaries(self):
        dtypes = "{name: str, age: int, height: float}"
        attr_name = "attribute"

        result = _extract_attributes(dtypes, attr_name)

        assert isinstance(result, list)
        for attribute in result:
            assert isinstance(attribute, dict)
            assert "name" in attribute
            assert "type" in attribute
            assert "required" in attribute
            assert attribute["name"] in ["name", "age", "height"]
            assert attribute["type"] in [["str"], ["int"], ["float"]]
            assert attribute["required"] == False

    # Raises a ValueError if an attribute in the small type string is not valid
    @pytest.mark.unit
    def test_raise_value_error_invalid_attribute(self):
        dtypes = "{name: str, age int, height: float}"
        attr_name = "attribute"

        with pytest.raises(ValueError):
            _extract_attributes(dtypes, attr_name)

    # Raises a ValueError if an attribute in the small type string has no name
    @pytest.mark.unit
    def test_raise_value_error_no_attribute_name(self):
        dtypes = "{: str, age: int, height: float}"
        attr_name = "attribute"

        with pytest.raises(AssertionError):
            _extract_attributes(dtypes, attr_name)

    # Test the input of a small type with a non-basic type
    @pytest.mark.unit
    def test_input_non_basic_type(self):
        dtypes = "{name: str, age: int, height: float, address: Address}"
        attr_name = "attribute"

        with pytest.raises(ValueError) as e:
            _extract_attributes(dtypes, attr_name)

        assert (
            str(e.value)
            == "Small type: Type 'Address' is not valid. Please, only use base datatypes for small types"
        )


class TestProcessSmallType:
    # Process a small type with valid syntax and return a dictionary with the expected keys and values
    @pytest.mark.unit
    def test_valid_syntax(self):
        dtypes = "{name: str}"
        object_stack = [{"attributes": [{"name": "attribute"}], "name": "object"}]
        expected_result = {
            "name": "Attribute",
            "origin": "object",
            "attr_name": "attribute",
            "attributes": [{"name": "name", "type": ["str"], "required": False}],
            "docstring": "Small type for attribute 'attribute'",
            "type": "object",
            "parent": None,
        }

        result = process_small_type(dtypes, object_stack)

        assert result == expected_result

    # Process a small type with multiple attributes and return a dictionary with the expected keys and values
    @pytest.mark.unit
    def test_multiple_attributes(self):
        dtypes = "{name: str, age: int}"
        object_stack = [{"attributes": [{"name": "attribute"}], "name": "object"}]
        expected_result = {
            "name": "Attribute",
            "origin": "object",
            "attr_name": "attribute",
            "attributes": [
                {"name": "name", "type": ["str"], "required": False},
                {"name": "age", "type": ["int"], "required": False},
            ],
            "docstring": "Small type for attribute 'attribute'",
            "type": "object",
            "parent": None,
        }

        result = process_small_type(dtypes, object_stack)

        assert result == expected_result

    # Raise a ValueError if the small type attribute is not valid
    @pytest.mark.unit
    def test_invalid_attribute(self):
        dtypes = "{: str}"
        object_stack = [{"attributes": [{"name": "attribute"}], "name": "object"}]

        with pytest.raises(AssertionError):
            process_small_type(dtypes, object_stack)

    # Raise a ValueError if the small type data type is not valid
    @pytest.mark.unit
    def test_invalid_data_type(self):
        dtypes = "{name: invalid}"
        object_stack = [{"attributes": [{"name": "attribute"}], "name": "object"}]

        with pytest.raises(ValueError):
            process_small_type(dtypes, object_stack)

    # Raise an AssertionError if the small type sub-attribute has no name
    @pytest.mark.unit
    def test_missing_sub_attribute_name(self):
        dtypes = "{: str}"
        object_stack = [{"attributes": [{"name": "attribute"}], "name": "object"}]

        with pytest.raises(AssertionError):
            process_small_type(dtypes, object_stack)
