import pytest
import json
from pydantic.fields import PrivateAttr
from sdRDM import DataModel

class TestTerms:

    def _setup(self):
        """Creates a simple model"""

        class Model(DataModel):
            name: str
            _repo: str = PrivateAttr(default="https://example.com")

        return Model

    def test_dynamic_attribute_term(self):
        """Tests whether a dynamic attribute term is correctly added to the JSON-LD output."""

        # Arrange
        Model = self._setup()

        # Act
        ds = Model(name="Test")
        ds.add_attribute_term("name", "https://example.com/Hello")

        # Assert
        expected = {
          "@context": {
            "Model": "https://example.com/Model",
            "name": {
              "@type": [
                "https://example.com/Hello"
              ]
            }
          },
          "@type": [
            "Model"
          ],
          "name": "Test"
        }

        assert json.loads(ds.json()) == expected, (
            "JSON LD does not match expected output and does not contain the correct term for the field"
        )

    def test_invalid_dynamic_attribute_term(self):
        """Tests whether an invalid dynamic attribute term is throwing an error."""

        # Arrange
        Model = self._setup()

        # Act
        ds = Model(name="Test")

        # Assert
        with pytest.raises(ValueError):
            ds.add_attribute_term("name", "Hello")

    def test_non_existent_dynamic_attribute_term(self):
        """Tests whether an invalid dynamic attribute term is throwing an error."""

        # Arrange
        Model = self._setup()

        # Act
        ds = Model(name="Test")

        # Assert
        with pytest.raises(AttributeError):
            ds.add_attribute_term("test", "Hello")


    def test_dynamic_object_term(self):
        """Tests whether a dynamic object term is correctly added to the JSON-LD output."""

        # Arrange
        Model = self._setup()

        # Act
        ds = Model(name="Test")
        ds.add_object_term("https://example.com/Hello")

        # Assert
        expected = {
          "@context": {
            "Model": "https://example.com/Model",
          },
          "@type": [
            "Model",
            "https://example.com/Hello"
          ],
          "name": "Test"
        }

        assert json.loads(ds.json()) == expected, (
            "JSON LD does not match expected output and does not contain the correct term for the field"
        )

    def test_invalid_dynamic_object_term(self):
        """Tests whether an invalid dynamic attribute term is throwing an error."""

        # Arrange
        Model = self._setup()

        # Act
        ds = Model(name="Test")

        # Assert
        with pytest.raises(ValueError):
            ds.add_object_term("Hello")
