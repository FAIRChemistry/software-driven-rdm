import pytest

from sdRDM.generator.classrender import get_object


class TestGetObject:
    # Returns the object with the given name if it exists in the list of objects.
    @pytest.mark.unit
    def test_returns_object_with_given_name_if_exists(self):
        objects = [
            {"name": "object1", "type": "type1", "attributes": {"attr1": "value1"}},
            {"name": "object2", "type": "type2", "attributes": {"attr2": "value2"}},
            {"name": "object3", "type": "type3", "attributes": {"attr3": "value3"}},
        ]
        expected_object = {
            "name": "object2",
            "type": "type2",
            "attributes": {"attr2": "value2"},
        }

        result = get_object("object2", objects)

        assert result == expected_object

    # Raises a ValueError if the object with the given name does not exist in the list of objects.
    @pytest.mark.unit
    def test_raises_value_error_if_object_with_given_name_does_not_exist(self):
        objects = [
            {"name": "object1", "type": "type1", "attributes": {"attr1": "value1"}},
            {"name": "object2", "type": "type2", "attributes": {"attr2": "value2"}},
            {"name": "object3", "type": "type3", "attributes": {"attr3": "value3"}},
        ]

        with pytest.raises(ValueError):
            get_object("object4", objects)

    # Raises a ValueError if the object is not found in the list of objects.
    @pytest.mark.unit
    def test_returns_value_error_if_object_not_found(self):
        objects = []

        with pytest.raises(ValueError) as e:
            get_object("object1", objects)

        assert str(e.value) == "Could not find object 'object1' in objects."
