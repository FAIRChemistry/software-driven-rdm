from markdown_it.token import Token
from sdRDM.markdown.enumutils import parse_markdown_enumerations


import pytest


class TestParseMarkdownEnumerations:
    # The function correctly parses enumerations defined in a markdown model.
    def test_correctly_parses_enumerations(self, correct_enum_tokens):
        """
        Tests whether enums are parsed correctly. The following markdown is used:

        ## Enumeration 1

        This is the docstring for Enumeration 1

        ```python
        KEY1 = "value1"
        KEY2 = "value2"
        ```

        ## Enumeration 2

        This is the docstring for Enumeration 2

        ```python
        KEY3 = "value3"
        KEY4 = "value4"
        ```
        """

        expected_result = [
            {
                "name": "Enumeration 1",
                "docstring": "This is the docstring for Enumeration 1",
                "mappings": [
                    {"key": "KEY1", "value": '"value1"'},
                    {"key": "KEY2", "value": '"value2"'},
                ],
                "type": "enum",
            },
            {
                "name": "Enumeration 2",
                "docstring": "This is the docstring for Enumeration 2",
                "mappings": [
                    {"key": "KEY3", "value": '"value3"'},
                    {"key": "KEY4", "value": '"value4"'},
                ],
                "type": "enum",
            },
        ]

        assert isinstance(parse_markdown_enumerations(correct_enum_tokens), list)
        assert all(
            isinstance(enum, dict)
            for enum in parse_markdown_enumerations(correct_enum_tokens)
        )

        assert parse_markdown_enumerations(correct_enum_tokens) == expected_result

    # The function raises an AssertionError if a mapping does not follow the syntax rules.
    def test_raises_assertion_error_for_invalid_mapping(
        self,
        incorrect_mapping_enum_tokens,
    ):
        with pytest.raises(AssertionError):
            parse_markdown_enumerations(incorrect_mapping_enum_tokens)

    # The function correctly handles empty enumerations (i.e. no mappings).
    def test_correctly_handles_empty_enumerations(
        self,
        empty_mapping_enum_tokens,
    ):
        expected_result = [
            {
                "name": "Enumeration 1",
                "docstring": "This is the docstring for Enumeration 1",
                "mappings": [],
                "type": "enum",
            },
            {
                "name": "Enumeration 2",
                "docstring": "This is the docstring for Enumeration 2",
                "mappings": [],
                "type": "enum",
            },
        ]

        assert parse_markdown_enumerations(empty_mapping_enum_tokens) == expected_result
