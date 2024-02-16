from typing import List, Union
from uuid import uuid4
import warnings

from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM import DataModel
from sdRDM.base.datatypes import Unit

import astropy
from astropy.units import Quantity as AstroQuantity


class Quantity(
    DataModel,
    nsmap={"": "https://www.github.com/software-driven-rdm"},
    tag="Quantity",
):
    """
    Represents a quantity with a value and a unit.

    Args:
        value (Union[float, int]): The numerical value of the quantity.
        unit (Union[str, astropy.units.UnitBase]): The unit of measurement for the quantity.

    Attributes:
        id (str): The unique identifier of the quantity.
        _quantity (AstroQuantity): The underlying astropy quantity object.

    Methods:
        __mul__(self, other): Multiply the quantity by another quantity or a scalar.
        __truediv__(self, other): Divide the quantity by another quantity or a scalar.
        __add__(self, other): Add the quantity to another quantity or a scalar.
        __sub__(self, other): Subtract another quantity or a scalar from the quantity.
    """

    id: str = attr(name="id", default_factory=lambda: str(uuid4()))

    value: Union[float, int] = attr(
        title="Value",
        description="The numerical value of the quantity.",
    )

    unit: Unit = element(
        title="Unit",
        description="The unit of measurement for the quantity.",
    )

    _quantity: AstroQuantity = PrivateAttr(default=None)

    def __init__(
        self,
        value: Union[float, int],
        unit: Union[str, Unit],
    ):
        super().__init__(value=value, unit=unit)

    @model_validator(mode="after")
    def _set_quantity(self):
        self._quantity = AstroQuantity(self.value, self.unit._unit)
        return self

    # dunders
    def __mul__(self, other):
        if isinstance(other, Quantity):
            new_quantity = self._quantity * other._quantity
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        if isinstance(other, (int, float)):
            new_quantity = self._quantity.value * other * self._quantity.unit
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        else:
            raise TypeError(
                "unsupported operand type(s) for *: 'Quantity' and '{}'".format(
                    type(other).__name__
                )
            )

    def __truediv__(self, other):
        if isinstance(other, Quantity):
            if other._quantity.value == 0:
                raise ZeroDivisionError("division by zero")

            new_quantity = (
                self._quantity.value
                / other._quantity.value
                * self._quantity.unit
                / other._quantity.unit
            )
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        if isinstance(other, (int, float)):
            if other == 0:
                raise ZeroDivisionError("division by zero")

            new_quantity = self._quantity.value / other * self._quantity.unit
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        raise TypeError(
            "unsupported operand type(s) for /: 'Quantity' and '{}'".format(
                type(other).__name__
            )
        )

    def __add__(self, other):
        if isinstance(other, Quantity) and self._quantity.unit == other._quantity.unit:
            new_quantity = (
                self._quantity.value + other._quantity.value
            ) * self._quantity.unit
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        if isinstance(other, (int, float)):
            new_quantity = (self._quantity.value + other) * self._quantity.unit
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        raise TypeError(
            "unsupported operand type(s) for +: 'Quantity' and '{}'".format(
                type(other).__name__
            )
        )

    def __sub__(self, other):
        if isinstance(other, Quantity) and self._quantity.unit == other._quantity.unit:
            new_quantity = self._quantity - other._quantity
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        if isinstance(other, (int, float)):
            new_quantity = (self._quantity.value - other) * self._quantity.unit
            return Quantity(
                value=new_quantity.value, unit=new_quantity.unit.to_string()
            )

        raise TypeError(
            "unsupported operand type(s) for -: 'Quantity' and '{}'".format(
                type(other).__name__
            )
        )

    def __eq__(self, other):
        if isinstance(other, Quantity):
            return self._quantity == other._quantity

        if isinstance(other, (int, float)):
            if not self.value == other:
                return False

            warnings.warn(
                "Comparing a Quantity object to a scalar. This is not recommended. "
                "Consider using the .value attribute to compare the value directly.",
                UserWarning,
            )
            return self.value == other

        raise TypeError(
            "unsupported operand type(s) for ==: 'Quantity' and '{}'".format(
                type(other).__name__
            )
        )

    def __ne__(self, other):
        return not self.__eq__(other)


if __name__ == "__main__":
    quantity = Quantity(value=1, unit="m")

    # JSON
    print(quantity.json(indent=2), end="\n\n")

    # XML
    print(quantity.xml(), end="\n\n")

    # YAML
    print(quantity.yaml(), end="\n\n")

    # Astropy Quantity object
    print("Quantity object: ", quantity._quantity, end="\n\n")
