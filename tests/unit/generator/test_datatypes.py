import pytest
from sdRDM.generator.datatypes import DataTypes


class TestDataTypes:
    # Test that each member of the DataTypes enum has a valid value attribute
    @pytest.mark.unit
    def test_valid_value_attribute(self):
        for member in DataTypes:
            assert member.value is not None

    # Test that the get_value_list method returns a list of all valid value attributes
    @pytest.mark.unit
    def test_get_value_list(self):
        assert DataTypes.get_value_list() == [member.value[0] for member in DataTypes]

    # Test that the string, str, float, int, integer, bytes, bool, and boolean members have a value attribute of None
    @pytest.mark.unit
    def test_none_value_attributes(self):
        assert DataTypes.string.value[1] is None
        assert DataTypes.str.value[1] is None
        assert DataTypes.float.value[1] is None
        assert DataTypes.int.value[1] is None
        assert DataTypes.integer.value[1] is None
        assert DataTypes.bytes.value[1] is None
        assert DataTypes.bool.value[1] is None
        assert DataTypes.boolean.value[1] is None
