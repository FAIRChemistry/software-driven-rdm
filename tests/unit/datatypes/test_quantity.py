from pydantic import ValidationError
import pytest

from sdRDM.base.datatypes.quantity import Quantity
from astropy.units import Unit as AstroUnit
from astropy.units import Quantity as AstroQuantity


class TestQuantity:

    # Creating a Quantity object with valid value and unit should set the value and unit attributes correctly.
    @pytest.mark.unit
    def test_valid_value_and_unit(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        assert quantity.value == value
        assert quantity.unit.name == unit

    # The __mul__ method should correctly multiply two Quantity objects and return a new Quantity object with the correct value and unit.
    @pytest.mark.unit
    def test_multiply_two_quantity_objects(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        result = quantity1 * quantity2

        assert result.value == value1 * value2
        assert result.unit._unit == AstroUnit(unit1) * AstroUnit(unit2)

    # The __mul__ method should correctly multiply a Quantity object with a scalar and return a new Quantity object with the correct value and unit.
    @pytest.mark.unit
    def test_multiply_quantity_with_scalar(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        scalar = 5

        result = quantity * scalar

        assert result.value == value * scalar
        assert result.unit.name == unit

    # Creating a Quantity object with a non-numeric value should raise a validation error.
    @pytest.mark.unit
    def test_non_numeric_value_validation_error(self):
        value = "invalid"
        unit = "m"

        with pytest.raises(ValidationError):
            Quantity(value, unit)

    # Creating a Quantity object with an invalid unit should raise a validation error.
    @pytest.mark.unit
    def test_invalid_unit_validation_error(self):
        value = 10
        unit = "invalid"

        with pytest.raises(ValueError):
            Quantity(value, unit)

    # The __mul__ method should raise a TypeError if the argument is not a Quantity object or a scalar.
    @pytest.mark.unit
    def test_multiply_invalid_argument_type_error(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        invalid_argument = "invalid"

        with pytest.raises(TypeError):
            quantity * invalid_argument

    @pytest.mark.unit
    def test_divide_invlid_type_error(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        invalid_argument = "invalid"

        with pytest.raises(TypeError):
            quantity / invalid_argument

    @pytest.mark.unit
    def test_add_invlid_type_error(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        invalid_argument = "invalid"

        with pytest.raises(TypeError):
            quantity + invalid_argument

    @pytest.mark.unit
    def test_subtract_invlid_type_error(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)

        invalid_argument = "invalid"

        with pytest.raises(TypeError):
            quantity - invalid_argument

    def test_divide_two_quantity_objects(self):
        # Create two Quantity objects
        q1 = Quantity(value=10, unit="m")
        q2 = Quantity(value=2, unit="s")

        # Divide q1 by q2
        result = q1 / q2

        # Check the value and unit of the result
        assert result.value == 5
        assert result.unit._unit == AstroUnit("m") / AstroUnit("s")

    def test_divide_quantity_by_scalar(self):
        # Create a Quantity object
        quantity = Quantity(value=10, unit="m")

        # Divide the quantity by a scalar
        result = quantity.__truediv__(2)

        # Check that the result is a Quantity object
        assert isinstance(result, Quantity)

        # Check that the value and unit of the result are correct
        assert result.value == 5
        assert result.unit.bases == quantity.unit.bases

    # The __add__ method should correctly add two Quantity objects with the same unit and return a new Quantity object with the correct value and unit.
    def test_add_method_with_same_unit(self):
        # Create two Quantity objects with the same unit
        q1 = Quantity(value=2, unit="m")
        q2 = Quantity(value=3, unit="m")

        # Add the two Quantity objects
        result = q1 + q2

        # Check that the result is a new Quantity object with the correct value and unit
        assert isinstance(result, Quantity)
        assert result.value == 5
        assert result.unit.bases == q1.unit.bases

    def test_add_scalar_to_quantity(self):
        # Create a Quantity object
        quantity = Quantity(value=10, unit="m")

        # Add a scalar to the Quantity object
        result = quantity + 5

        # Check that the result is a Quantity object
        assert isinstance(result, Quantity)

        # Check that the value and unit of the result are correct
        assert result.value == 15
        assert result.unit.bases == quantity.unit.bases

    def test_subtract_two_quantity_objects_with_same_unit(self):
        # Create two Quantity objects with the same unit
        q1 = Quantity(value=10, unit="m")
        q2 = Quantity(value=5, unit="m")

        # Subtract q2 from q1
        result = q1 - q2

        # Check that the result is a Quantity object
        assert isinstance(result, Quantity)

        # Check that the value and unit of the result are correct
        assert result.value == 5
        assert result.unit.bases == q1.unit.bases

    def test_subtract_scalar_from_quantity(self):
        # Create a Quantity object
        quantity = Quantity(value=10, unit="m")

        # Subtract a scalar from the Quantity object
        result = quantity - 5

        # Check that the result is a Quantity object
        assert isinstance(result, Quantity)

        # Check that the value and unit of the result are correct
        assert result.value == 5
        assert result.unit.bases == quantity.unit.bases

    # subtracting a quantity object from another quantity object with different units should raise a ValueError
    @pytest.mark.unit
    def test_subtract_quantity_objects_with_different_units(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        with pytest.raises(TypeError):
            quantity1 - quantity2

    # adding a quantity object to another quantity object with different units should raise a ValueError
    @pytest.mark.unit
    def test_add_quantity_objects_with_different_units(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        with pytest.raises(TypeError):
            quantity1 + quantity2

    # _set_quantity sets the _quantity attribute of Quantity instance with an AstroQuantity object created from the value and unit attributes
    def test_set_quantity_sets_quantity_attribute(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)
        quantity._set_quantity()
        assert isinstance(quantity._quantity, AstroQuantity)

    # test division by zero scalar
    @pytest.mark.unit
    def test_division_by_zero_scalar(self):
        value = 10
        unit = "m"
        quantity = Quantity(value, unit)
        with pytest.raises(ZeroDivisionError):
            quantity / 0

    # test division by zero quantity
    @pytest.mark.unit
    def test_division_by_zero_quantity(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 0
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        with pytest.raises(ZeroDivisionError):
            quantity1 / quantity2

    @pytest.mark.unit
    def test_multiplication_with_different_units(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        new_quantity = quantity1 * quantity2
        assert new_quantity.value == value1 * value2
        assert new_quantity.unit._unit == AstroUnit(unit1) * AstroUnit(unit2)

    # test division with different units
    @pytest.mark.unit
    def test_division_with_different_units(self):
        value1 = 10
        unit1 = "mmol / l"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "l"
        quantity2 = Quantity(value2, unit2)

        new_quantity = quantity1 / quantity2
        assert new_quantity.value == value1 / value2
        assert new_quantity.unit._unit == AstroUnit(unit1) / AstroUnit(unit2)

    # test raise error bitwise operation
    @pytest.mark.unit
    def test_bitwise_operation_error(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        with pytest.raises(TypeError):
            quantity1 & quantity2

    # test raise error module operation
    @pytest.mark.unit
    def test_module_operation_error(self):
        value1 = 10
        unit1 = "m"
        quantity1 = Quantity(value1, unit1)

        value2 = 5
        unit2 = "s"
        quantity2 = Quantity(value2, unit2)

        with pytest.raises(TypeError):
            quantity1 % quantity2

    # Two Quantity objects with the same value and unit should be equal.
    @pytest.mark.unit
    def test_same_value_and_unit(self):
        quantity1 = Quantity(value=10, unit="m")
        quantity2 = Quantity(value=10, unit="m")
        assert quantity1 == quantity2

    @pytest.mark.unit
    def test_compare_to_self(self):
        quantity = Quantity(value=10, unit="m")
        assert quantity == quantity

    @pytest.mark.unit
    def test_compare_to_scalar_with_same_value(self):
        quantity = Quantity(value=10, unit="m")
        scalar = 10
        assert quantity == scalar

    @pytest.mark.unit
    def test_compare_to_scalar_with_nan_value(self):
        quantity = Quantity(value=float("nan"), unit="m")
        scalar = float("nan")
        assert quantity != scalar

    @pytest.mark.unit
    def test_compare_to_scalar_with_infinity_value(self):
        quantity = Quantity(value=float("inf"), unit="m")
        scalar = float("inf")
        assert quantity == scalar

    @pytest.mark.unit
    def test_comparing_quantity_to_scalar_with_different_value_should_return_false(
        self,
    ):
        quantity = Quantity(value=10, unit="m")
        scalar = 5
        assert quantity != scalar

    @pytest.mark.unit
    def test_comparing_quantity_to_none(self):
        quantity = Quantity(value=10, unit="m")
        with pytest.raises(TypeError):
            quantity == None

    @pytest.mark.unit
    def test_different_values(self):
        quantity1 = Quantity(value=10, unit="m")
        quantity2 = Quantity(value=20, unit="m")
        assert quantity1.__eq__(quantity2) == False

    @pytest.mark.unit
    def test_different_units(self):
        quantity1 = Quantity(value=10, unit="m")
        quantity2 = Quantity(value=10, unit="s")
        assert quantity1.__eq__(quantity2) == False

    @pytest.mark.unit
    def test_comparing_quantity_to_scalar_with_non_float_value_should_raise_type_error(
        self,
    ):
        quantity = Quantity(value=10, unit="m")
        scalar = "abc"
        with pytest.raises(TypeError):
            quantity.__eq__(scalar)
