import re
import pytest

from sdRDM.generator.classrender import render_attribute

class TestAttrRender:
    @pytest.mark.unit
    def test_description_is_added(self):
        # Arrange
        attribute = {
            "description": 'This is a "description"',
            "type": ["str"],
            "required": False,
            "name": "name",
        }

        # Act
        method = render_attribute(
            attribute=attribute,
            objects=[],
            obj_name="Test",
        )

        # Assert
        expected = """name:Optional[str]=element(default=None,description="Thisisa'description'",tag="name",json_schema_extra=dict(),)"""
        assert re.sub(r"\s|\n", "", method) == expected
