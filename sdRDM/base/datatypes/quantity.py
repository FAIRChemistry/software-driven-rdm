from typing import List, Union
from uuid import uuid4

from pydantic import PrivateAttr, computed_field
from pydantic_xml import attr, element, wrapped
import sdRDM
from sdRDM.base.datatypes.unit import Unit

import astropy
from astropy.units import Quantity as AstroQuantity


class Quantity(
    sdRDM.DataModel,
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

    Properties:
        value (Union[float, int]): The numerical value of the quantity.
        unit (astropy.units.UnitBase): The unit of measurement for the quantity.

    Methods:
        __mul__(self, other): Multiply the quantity by another quantity or a scalar.
        __truediv__(self, other): Divide the quantity by another quantity or a scalar.
        __add__(self, other): Add the quantity to another quantity or a scalar.
        __sub__(self, other): Subtract another quantity or a scalar from the quantity.
    """

    id: str = attr(name="id", default_factory=lambda: str(uuid4()))
    _quantity: AstroQuantity = PrivateAttr()

    def __init__(
        self,
        value: Union[float, int],
        unit: Union[str, astropy.units.UnitBase],
    ):
        super().__init__()
        if isinstance(unit, str):
            unit = astropy.units.Unit(unit)
        self._quantity = value * unit

    @computed_field
    def value(self) -> Union[float, int]:
        return self._quantity.value

    @value.setter
    def value(self, value):
        self._quantity = value * self._quantity.unit

    @computed_field
    def unit(self) -> astropy.units.UnitBase:
        return Unit.from_string(str(self._quantity.unit))

    @unit.setter
    def unit(self, unit):
        if isinstance(unit, str):
            unit = astropy.units.Unit(unit)
        self._quantity = self._quantity.to(unit)

    # dunders
    def __mul__(self, other):
        if isinstance(other, Quantity):
            new_quantity = self._quantity * other._quantity
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

        if isinstance(other, (int, float)):
            new_quantity = self._quantity.value * other * self._quantity.unit
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

    def __truediv__(self, other):
        if isinstance(other, Quantity):
            new_quantity = (
                self._quantity.value
                / other._quantity.value
                * self._quantity.unit
                / other._quantity.unit
            )
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

        if isinstance(other, (int, float)):
            new_quantity = self._quantity.value / other * self._quantity.unit
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

    def __add__(self, other):
        if isinstance(other, Quantity) and self._quantity.unit == other._quantity.unit:
            new_quantity = (
                self._quantity.value + other._quantity.value
            ) * self._quantity.unit
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

        if isinstance(other, (int, float)):
            new_quantity = (self._quantity.value + other) * self._quantity.unit
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

    def __sub__(self, other):
        if isinstance(other, Quantity) and self._quantity.unit == other._quantity.unit:
            new_quantity = self._quantity - other._quantity
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)

        if isinstance(other, (int, float)):
            new_quantity = self._quantity - other
            return Quantity(value=new_quantity.value, unit=new_quantity.unit)
