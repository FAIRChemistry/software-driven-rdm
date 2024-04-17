import json
import re
import pytest

from sdRDM.base.datatypes.unit import BaseUnit, Unit
from astropy.units import UnitBase, Unit as AstroUnit


class TestUnit:
    @pytest.mark.unit
    def test_simple_unit_from_string(self):
        # Arrange
        unit_string = "m"

        # Act
        unit = Unit.from_string(unit_string)

        # Assert
        assert unit.name == "m"
        assert unit.bases == [
            BaseUnit(
                kind="m",
                exponent=1,
                scale=1,
            )
        ]

    @pytest.mark.unit
    def test_composite_unit_from_string(self):
        # Arrange
        unit_string = "m/s"

        # Act
        unit = Unit.from_string(unit_string)

        # Assert
        assert unit.name == "m / s"
        assert unit.bases == [
            BaseUnit(
                kind="m",
                exponent=1,
                scale=1,
            ),
            BaseUnit(
                kind="s",
                exponent=-1,
                scale=1,
            ),
        ]

    @pytest.mark.unit
    def test_dimensionless_unit_from_string(self):
        # Arrange
        unit_string = "dimensionless"

        # Act
        unit = Unit.from_string(unit_string)

        # Assert
        assert unit.name == "dimensionless"
        assert unit.bases == []

    @pytest.mark.unit
    def test_json_serialization(self):
        # Arrange
        unit_string = "m/s"

        # Act
        unit = Unit.from_string(unit_string)
        unit_json = unit.json(exclude={"id"})

        # Assert
        expected_json = {
            '@context': {
                'Unit': 'https://www.github.com/JR-1991/software-driven-rdm/Unit',
            },
            "name": "m / s",
            "bases": [
                {
                    "@context": {
                        "BaseUnit": "https://www.github.com/JR-1991/software-driven-rdm/BaseUnit",
                    },
                    "kind": "m",
                    "exponent": 1.0,
                    "scale": 1.0,
                },
                {
                    "@context": {
                        "BaseUnit": "https://www.github.com/JR-1991/software-driven-rdm/BaseUnit",
                    },
                    "kind": "s",
                    "exponent": -1.0,
                    "scale": 1.0,
                },
            ],
        }

        assert json.loads(unit_json) == expected_json

    @pytest.mark.unit
    def test_to_unit_string(self):
        # Arrange
        unit_string = "m/s"
        unit = Unit.from_string(unit_string)

        # Act
        string = unit.to_unit_string()

        # Assert
        assert string == "m / s"

    @pytest.mark.unit
    def test_xml_serialization(self):
        # Arrange
        unit_string = "m/s"

        # Act
        unit = Unit.from_string(unit_string)
        unit_xml = unit.xml()

        # Assert
        expected_xml = '<?xml version="1.0" encoding="UTF-8"?><Unit  name="m / s">  <listOfUnits>    <unit scale="1.0" kind="m" exponent="1.0"/>    <unit scale="1.0" kind="s" exponent="-1.0"/>  </listOfUnits></Unit>'

        unit_xml = unit_xml.replace("\n", "").replace("'", '"')
        unit_xml = re.sub(r'id="[\w-]+"', "", unit_xml)

        assert unit_xml == expected_xml
