import sdRDM

from typing import Union
from astropy.units import UnitBase, Unit, CompositeUnit
from pydantic import field_serializer, field_validator, PrivateAttr


class UnitType(sdRDM.DataModel):
    """
    Represents a unit type.

    Attributes:
        scale (float): The scale of the unit.
        bases (list[Union[str, UnitBase]]): The bases of the unit.
        powers (list[float]): The powers of the unit.
        _unit (Union[UnitBase, UnitBase]): The internal unit object.

    Methods:
        _serialize_bases: Serializes the bases of the unit.
        from_string: Creates a Unit object from a string representation.
        from_astropy_unit: Creates an instance of the class from an Astropy unit.
        to_unit_string: Returns a string representation of the unit.
    """

    scale: float
    bases: list[Union[str, UnitBase]]
    powers: list[float]
    _unit: Union[UnitBase, UnitBase] = PrivateAttr()
    _hash: int = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._unit = CompositeUnit(
            scale=self.scale,
            bases=self.bases,
            powers=self.powers,
        )

        self._hash = hash(self._unit)

    @field_validator("bases", mode="before")
    @classmethod
    def _bases_to_astropy(cls, v):
        """
        Convert a list of bases to Astropy units.

        Args:
            v (list): List of bases.

        Returns:
            list: List of Astropy units.
        """
        return [Unit(base) for base in v]

    @field_serializer("bases")
    def _serialize_bases(self, bases: list[Union[str, UnitBase]]):
        return [str(base) for base in bases]

    @classmethod
    def from_string(cls, unit_string: str):
        """
        Creates a Unit object from a string representation.

        Args:
            unit_string (str): The string representation of the unit.

        Returns:
            Unit: The created Unit object.

        Raises:
            AssertionError: If the unit is not a UnitBase or Unit.
        """
        unit = Unit(unit_string)

        unit_class = cls(
            scale=unit.si._scale,  # type: ignore
            bases=unit.si._bases,  # type: ignore
            powers=unit.si._powers,  # type: ignore
        )

        assert isinstance(unit, (UnitBase, Unit)), "Unit must be a UnitBase or Unit."

        unit_class._unit = unit

        return unit_class

    @classmethod
    def from_astropy_unit(cls, unit: Union[UnitBase, Unit]):
        """
        Creates an instance of the class from an Astropy unit.

        Args:
            unit (Union[UnitBase, Unit]): The Astropy unit to convert.

        Returns:
            The converted instance of the class.

        Raises:
            AssertionError: If the unit is not an instance of UnitBase or Unit.
        """
        unit_class = cls(
            scale=unit.si._scale,  # type: ignore
            bases=unit.si._bases,  # type: ignore
            powers=unit.si._powers,  # type: ignore
        )

        assert isinstance(unit, (UnitBase, Unit)), "Unit must be a UnitBase or Unit."

        unit_class._unit = unit

        return unit_class

    def to_unit_string(self):
        """
        Returns a string representation of the unit.

        Returns:
            str: The unit as a string.
        """
        return str(self._unit)
