from uuid import uuid4
from pydantic_xml import attr, element, wrapped
import sdRDM

from typing import List, Union
from astropy.units import UnitBase, Unit as AstroUnit
from pydantic import field_serializer, PrivateAttr


class BaseUnit(
    sdRDM.DataModel,
    tag="BaseUnit",
):
    scale: float = attr(name="scale")
    kind: Union[str, AstroUnit, UnitBase] = attr(name="kind")
    exponent: float = attr(name="exponent")

    @field_serializer("kind")
    def _serialize_kind(self, v):
        if isinstance(self.kind, str):
            return self.kind
        else:
            return str(self.kind)


class Unit(
    sdRDM.DataModel,
    nsmap={"": "https://www.github.com/software-driven-rdm"},
    tag="Unit",
):
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

    id: str = attr(name="id", default_factory=lambda: str(uuid4()))
    name: str = attr(name="name")
    bases: List[BaseUnit] = element()
    _unit: UnitBase = PrivateAttr()
    _hash: int = PrivateAttr()

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
        unit = AstroUnit(unit_string)

        assert isinstance(
            unit, (UnitBase, AstroUnit)
        ), "Unit must be a UnitBase or Unit."

        return cls.from_astropy_unit(unit)

    @classmethod
    def from_astropy_unit(cls, unit: Union[UnitBase, AstroUnit]):
        """
        Creates an instance of the class from an Astropy unit.

        Args:
            unit (Union[UnitBase, Unit]): The Astropy unit to convert.

        Returns:
            The converted instance of the class.

        Raises:
            AssertionError: If the unit is not an instance of UnitBase or Unit.
        """

        assert isinstance(
            unit, (UnitBase, AstroUnit)
        ), "Unit must be a UnitBase or Unit."

        unit_class = cls(
            name=str(unit),
            bases=cls._convert_unit_to_base_units(unit),
        )
        unit_class._unit = unit

        return unit_class

    def to_unit_string(self):
        """
        Returns a string representation of the unit.

        Returns:
            str: The unit as a string.
        """
        return str(self._unit)

    @classmethod
    def _convert_unit_to_base_units(cls, unit):
        """
        Converts a given unit to its base units.

        Parameters:
        unit (Unit): The unit to be converted.

        Returns:
        list: A list of base units.

        """
        base_units = []

        if not hasattr(unit, "_powers"):
            powers = [1.0]
        else:
            powers = unit._powers

        for base, power in zip(unit.bases, powers):
            if base._long_names == ["liter"]:
                base_units.append(cls._construct_base_unit(base, power))
            elif not hasattr(base, "_represents"):
                base_units.append(cls._construct_base_unit(base, power))
            else:
                reduced_unit = base._represents
                base_units.append(
                    cls._construct_base_unit(reduced_unit, power),
                )

        return base_units

    @staticmethod
    def _construct_base_unit(unit: UnitBase, power: float):
        """
        Decomposes a unit into its scale, exponent, and kind.

        Args:
            unit: The unit to be decomposed.
            power: The exponent of the unit.

        Returns:
            A dictionary containing the scale, exponent, and kind of the unit.
        """

        if not hasattr(unit, "_bases"):
            kind = unit
        else:
            kind = unit._bases[0]  # type: ignore

        return BaseUnit(
            scale=float(unit.scale),
            exponent=power,
            kind=kind,
        )
