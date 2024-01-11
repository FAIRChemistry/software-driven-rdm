import pytest

from markdown_it.token import Token
from sdRDM.markdown.objectutils import (
    add_module_name_to_objects,
    attribute_has_default,
    check_previous_attribute,
    gather_objects_to_keep,
    get_attribute_name,
    get_object_name,
    get_parent,
    has_parent,
    has_small_type,
    is_linked_type,
    is_reference_type,
    is_remote_type,
    is_required,
    process_attribute,
    process_description,
    process_object,
    process_option,
    process_type_option,
)


class TestIsLinkedType:
    # Returns True if the given type is a markdown link
    @pytest.mark.unit
    def test_returns_true_if_type_is_markdown_link(self):
        # Arrange
        dtype = "[Object](#object)"

        # Act
        result = is_linked_type(dtype)

        # Assert
        assert result == True

    # Returns False if the given type is not a markdown link
    @pytest.mark.unit
    def test_returns_false_if_type_is_not_markdown_link(self):
        # Arrange
        dtype = "int"

        # Act
        result = is_linked_type(dtype)

        # Assert
        assert result == False

    # Returns False if the given type is an empty string
    @pytest.mark.unit
    def test_returns_false_if_type_is_empty_string(self):
        # Arrange
        dtype = ""

        # Act
        result = is_linked_type(dtype)

        # Assert
        assert result == False


class TestIsReferenceType:
    # Returns True for a string that matches the reference type pattern.
    @pytest.mark.unit
    def test_returns_true_for_matching_reference_type_pattern(self):
        dtype = "@ReferenceType.attribute"
        assert is_reference_type(dtype) is True

    # Returns False for a string that does not match the reference type pattern.

    @pytest.mark.unit
    def test_returns_false_for_non_matching_reference_type_pattern(self):
        dtype = "NotReferenceType"
        assert is_reference_type(dtype) is False

    # Returns False for an empty string.
    @pytest.mark.unit
    def test_returns_false_for_empty_string(self):
        dtype = ""
        assert is_reference_type(dtype) is False

    # Returns False for a string that contains only whitespace characters.
    @pytest.mark.unit
    def test_returns_false_for_whitespace_string(self):
        dtype = "   "
        assert is_reference_type(dtype) is False


class TestHasSmallType:
    # Returns True if the input string contains a small type pattern.
    @pytest.mark.unit
    def test_contains_small_type_pattern(self):
        dtype = "{name: type}"
        assert has_small_type(dtype) is True

        dtype = "{name: type, name2: type2}"
        assert has_small_type(dtype) is True

        dtype = "{name: type, name2: type2, name3: type3}"
        assert has_small_type(dtype) is True

        dtype = "name: type"
        assert has_small_type(dtype) is False

        dtype = ""
        assert has_small_type(dtype) is False

        dtype = "   "
        assert has_small_type(dtype) is False

        dtype = "{name: type"
        assert has_small_type(dtype) is False

        dtype = "{name: }"
        assert has_small_type(dtype) is True


class TestIsRemoteType:
    # Returns True when given a valid remote type URL.
    @pytest.mark.unit
    def test_valid_remote_type_url(self):
        assert is_remote_type("https://github.com/username/repo.git@obj") == True

    # Returns False when given an invalid remote type URL.
    @pytest.mark.unit
    def test_invalid_remote_type_url(self):
        assert is_remote_type("https://github.com/username/repo@obj") == False

    # Returns False when given an empty string.
    @pytest.mark.unit
    def test_empty_string(self):
        assert is_remote_type("") == False

    # Returns False when given a non-string input.
    @pytest.mark.unit
    def test_non_string_input(self):
        assert is_remote_type(123) == False

    # Returns False when given a local type URL.
    @pytest.mark.unit
    def test_local_type_url(self):
        assert is_remote_type("file:///path/to/repo.git@branch") == False

    # Returns False when given a URL with an invalid format.
    @pytest.mark.unit
    def test_invalid_url_format(self):
        assert is_remote_type("https://github.com/username/repo.git") == False


class TestHasSmallType:
    # Returns True when input string contains a small type pattern.
    @pytest.mark.unit
    def test_contains_small_type_pattern(self):
        assert has_small_type("{name: type, name: type}") == True
        assert has_small_type("{name: type}") == True
        assert has_small_type("{name: type, name: type, ...}") == True
        assert has_small_type("{name: type, name: type, ...") == False
        assert has_small_type("name: type, name: type}") == False
        assert has_small_type("") == False
        assert has_small_type("   ") == False

    # Returns False when input string does not contain a small type pattern.
    @pytest.mark.unit
    def test_does_not_contain_small_type_pattern(self):
        assert has_small_type("name: type") == False
        assert has_small_type("name: type, name: type") == False
        assert has_small_type("name: type, name: type, ...") == False
        assert has_small_type("name: type, name: type, ...") == False
        assert has_small_type("name: type, name: type, ...") == False

    # Returns False when input string is empty.
    @pytest.mark.unit
    def test_empty_string(self):
        assert has_small_type("") == False

    # Returns False when input string contains only whitespace characters.
    @pytest.mark.unit
    def test_whitespace_string(self):
        assert has_small_type("   ") == False

    # Returns False when input string contains an opening brace but no closing brace.
    @pytest.mark.unit
    def test_missing_closing_brace(self):
        assert has_small_type("{name: type") == False

    # Returns False when input string contains a closing brace but no opening brace.
    @pytest.mark.unit
    def test_missing_opening_brace(self):
        assert has_small_type("name: type}") == False


class TestAttributeHasDefault:
    # Returns True if the current attribute has a default value
    @pytest.mark.unit
    def test_returns_true_if_attribute_has_default(self):
        object_stack = [{"attributes": [{"default": "default_value"}]}]
        assert attribute_has_default(object_stack) is True

    # Returns False if the current attribute does not have a default value
    @pytest.mark.unit
    def test_returns_false_if_attribute_does_not_have_default(self):
        object_stack = [{"attributes": [{"name": "attribute_name"}]}]
        assert attribute_has_default(object_stack) is False

    # Returns False if object_stack is empty
    @pytest.mark.unit
    def test_returns_false_if_object_stack_is_empty(self):
        object_stack = []
        assert attribute_has_default(object_stack) is False

    # Returns False if attributes list is empty
    @pytest.mark.unit
    def test_returns_false_if_attributes_list_is_empty(self):
        object_stack = [{"attributes": []}]
        assert attribute_has_default(object_stack) is False

    # Returns False if the last attribute in the attributes list does not have a 'default' key
    @pytest.mark.unit
    def test_returns_false_if_last_attribute_does_not_have_default_key(self):
        object_stack = [{"attributes": [{"name": "attribute_name"}]}]
        assert attribute_has_default(object_stack) is False

    # Returns True if the last attribute in the attributes list has a 'default_factory' key
    @pytest.mark.unit
    def test_returns_true_if_last_attribute_has_default_factory_key(self):
        object_stack = [{"attributes": [{"default_factory": "default_factory_value"}]}]
        assert attribute_has_default(object_stack) is True


class TestProcessTypeOption:
    # Processes a single type option with no subtypes or references
    @pytest.mark.unit
    def test_single_type_no_subtypes_or_references(self):
        # Arrange
        dtypes = "int"
        object_stack = [
            {
                "name": "Name",
                "attributes": [
                    {
                        "name": "attr_name",
                    }
                ],
            }
        ]
        external_types = {}

        # Act
        result = process_type_option(dtypes, object_stack, external_types)

        # Assert
        assert result == ["int"]

    # Processes multiple type options with no subtypes or references
    @pytest.mark.unit
    def test_multiple_types_no_subtypes_or_references(self):
        # Arrange
        dtypes = "int, float, str"
        object_stack = [
            {
                "name": "Name",
                "attributes": [
                    {
                        "name": "attr_name",
                    }
                ],
            }
        ]
        external_types = {}

        # Act
        result = process_type_option(dtypes, object_stack, external_types)

        # Assert
        assert result == ["int", "float", "str"]

    # Raises an AssertionError when processing a reference type with an invalid syntax
    @pytest.mark.unit
    def test_reference_type_invalid_syntax(self):
        # Arrange
        dtypes = "ReferenceType.invalid"
        object_stack = object_stack = [
            {
                "name": "Name",
                "attributes": [
                    {
                        "name": "attr_name",
                    }
                ],
            }
        ]
        external_types = {}

        # Act & Assert
        with pytest.raises(ValueError):
            process_type_option(dtypes, object_stack, external_types)

    # Does not add empty types to the processed types list
    @pytest.mark.unit
    def test_empty_types_not_added_to_processed_list(self):
        # Arrange
        dtypes = "int, , float, , str"
        object_stack = object_stack = [
            {
                "name": "Name",
                "attributes": [
                    {
                        "name": "attr_name",
                    }
                ],
            }
        ]
        external_types = {}

        # Act
        result = process_type_option(dtypes, object_stack, external_types)

        # Assert
        assert result == ["int", "float", "str"]

    @pytest.mark.unit
    def test_small_type_added_to_processed_types(self):
        # Arrange
        dtypes = "{name: integer}"
        object_stack = [
            {
                "name": "Name",
                "subtypes": [],
                "attributes": [
                    {
                        "name": "attr_name",
                        "default": "default_value",
                    }
                ],
            }
        ]

        external_types = {}

        # Act
        result = process_type_option(dtypes, object_stack, external_types)

        # Assert
        assert result == ["AttrName"]


class TestProcessOption:
    # Successfully processes a valid option and adds it to the recent attribute of the recent object
    @pytest.mark.unit
    def test_valid_option_added_to_attribute(self, correct_option):
        object_stack = [
            {
                "attributes": [
                    {
                        "name": "attribute_name",
                        "default": "default_value",
                    }
                ]
            }
        ]
        external_types = {}

        process_option(correct_option, object_stack, external_types)

        assert object_stack[-1]["attributes"][-1]["option"] == "value"

    # Handles the 'type' option correctly by calling 'process_type_option' and adding the result to the attribute
    @pytest.mark.unit
    def test_type_option_processed_correctly(self, type_option):
        object_stack = [
            {
                "attributes": [
                    {
                        "name": "attribute_name",
                        "default": "default_value",
                    }
                ]
            }
        ]
        external_types = {}

        process_option(type_option, object_stack, external_types)

        assert object_stack[-1]["attributes"][-1]["type"] == ["int"]

    # Handles the 'multiple' option correctly by deleting the default value and adding a 'ListPlus()' default factory to the attribute
    @pytest.mark.unit
    def test_multiple_option_processed_correctly(self, multiple_option):
        object_stack = [{"attributes": [{"default": "default_value"}]}]
        external_types = {}

        process_option(multiple_option, object_stack, external_types)

        assert "default" not in object_stack[-1]["attributes"][-1]
        assert object_stack[-1]["attributes"][-1]["default_factory"] == "ListPlus()"

    # Raises an AssertionError if the option content does not match the expected pattern
    @pytest.mark.unit
    def test_assertion_error_raised_for_invalid_option(self, invalid_option):
        object_stack = [{"attributes": []}]
        external_types = {}

        with pytest.raises(AssertionError):
            process_option(invalid_option, object_stack, external_types)


class TestIsRequired:
    # Returns True if a bold element is present in the list of children
    @pytest.mark.unit
    def test_returns_true_if_bold_element_present(
        self,
        required_token,
        non_required_token,
    ):
        # Arrange
        children = [required_token, non_required_token]

        # Act
        result = is_required(children)

        # Assert
        assert result == True

    # Returns False if no bold element is present in the list of children
    @pytest.mark.unit
    def test_returns_false_if_no_bold_element_present(self, non_required_token):
        # Arrange
        children = [non_required_token]

        # Act
        result = is_required(children)

        # Assert
        assert result == False

    # Handles a single bold element in the list of children
    @pytest.mark.unit
    def test_handles_single_bold_element(self, required_token):
        # Arrange
        children = [required_token]

        # Act
        result = is_required(children)

        # Assert
        assert result == True

    # Handles an empty list of children
    @pytest.mark.unit
    def test_handles_empty_list_of_children(self):
        # Arrange
        children = []

        # Act
        result = is_required(children)

        # Assert
        assert result == False

    # Handles a list of children with no bold elements
    @pytest.mark.unit
    def test_handles_list_with_no_bold_elements(self, non_required_token):
        # Arrange
        children = [non_required_token, non_required_token]

        # Act
        result = is_required(children)

        # Assert
        assert result == False


class TestGetAttributeName:
    # Returns the name of the first child element with type "text" and non-empty content
    @pytest.mark.unit
    def test_returns_name_of_first_child_with_non_empty_content(
        self,
        attribute_token,
    ):
        children = [
            attribute_token("attribute1"),
        ]
        result = get_attribute_name(children)
        assert result == "attribute1"

    # Handles a list of children with multiple elements of type "text" and non-empty content
    @pytest.mark.unit
    def test_handles_list_of_children_with_multiple_elements_with_non_empty_content(
        self,
        attribute_token,
    ):
        children = [
            attribute_token("attribute1"),
            attribute_token("attribute2"),
            attribute_token("attribute2"),
        ]
        result = get_attribute_name(children)
        assert result == "attribute1"

    # Handles a list of children with elements of type "text" and empty content
    @pytest.mark.unit
    def test_handles_list_of_children_with_elements_with_empty_content(
        self,
        attribute_token,
        empty_attribute_token,
    ):
        children = [
            empty_attribute_token,
            attribute_token("attribute2"),
            empty_attribute_token,
        ]
        result = get_attribute_name(children)
        assert result == "attribute2"

    # Raises an exception if the input list is empty
    @pytest.mark.unit
    def test_raises_exception_if_input_list_is_empty(self):
        children = []
        with pytest.raises(ValueError):
            get_attribute_name(children)

    # Raises an exception if none of the child elements have type "text"
    @pytest.mark.unit
    def test_raises_exception_if_none_of_child_elements_have_type_text(
        self,
        attribute_token_wrong_type,
    ):
        children = [
            attribute_token_wrong_type("attribute1"),
            attribute_token_wrong_type("attribute2"),
            attribute_token_wrong_type("attribute3"),
        ]

        with pytest.raises(ValueError):
            get_attribute_name(children)

    # Raises an exception if all child elements have empty content
    @pytest.mark.unit
    def test_raises_exception_if_all_child_elements_have_empty_content(
        self,
        empty_attribute_token,
    ):
        children = [
            empty_attribute_token,
            empty_attribute_token,
            empty_attribute_token,
        ]
        with pytest.raises(ValueError):
            get_attribute_name(children)


class TestProcessDescription:
    # If object_stack is not empty, append element content to the docstring of the recent object in object_stack
    @pytest.mark.unit
    def test_append_content_to_docstring(self):
        element = Token("type", "tag", 0, content="This is a description")
        object_stack = [{"docstring": "Initial docstring"}]

        process_description(element, object_stack)

        assert object_stack[-1]["docstring"] == "Initial docstringThis is a description"

    # If object_stack is empty, do nothing
    @pytest.mark.unit
    def test_do_nothing_if_object_stack_empty(self):
        element = Token("type", "tag", 0, content="This is a description")
        object_stack = []

        process_description(element, object_stack)

        assert object_stack == []

    # Ensure that the docstring of the recent object in object_stack is updated with the content of the element
    @pytest.mark.unit
    def test_update_docstring_with_element_content(self):
        element = Token(
            type="type", tag="tag", nesting=0, content="This is a description"
        )
        object_stack = [{"docstring": "Initial docstring"}]

        process_description(element, object_stack)

        assert object_stack[-1]["docstring"] == "Initial docstringThis is a description"

    # element has no content
    @pytest.mark.unit
    def test_element_has_no_content(self):
        element = Token(type="", tag="", nesting=0, content="")
        object_stack = [{"docstring": "Initial docstring"}]

        process_description(element, object_stack)

        assert object_stack[-1]["docstring"] == "Initial docstring"

    # object_stack is empty
    @pytest.mark.unit
    def test_object_stack_empty(self):
        element = Token(
            type="some_type", tag="some_tag", nesting=0, content="This is a description"
        )
        object_stack = []

        process_description(element, object_stack)

        assert object_stack == []

    # Verify that the function does not modify any other attributes of the recent object in object_stack
    @pytest.mark.unit
    def test_no_modification_of_other_attributes(self):
        element = Token(
            type="some_type", tag="some_tag", nesting=0, content="This is a description"
        )
        object_stack = [
            {
                "docstring": "Initial docstring",
                "attributes": [
                    {
                        "name": "attribute_name",
                        "default": "default_value",
                        "type": ["int"],
                    }
                ],
            }
        ]

        process_description(element, object_stack)

        assert object_stack[-1]["docstring"] == "Initial docstringThis is a description"
        assert object_stack[-1]["attributes"] == [
            {
                "name": "attribute_name",
                "default": "default_value",
                "type": ["int"],
            }
        ]


class TestProcessAttribute:
    # Adds a new attribute to the most recent object in the object stack.
    @pytest.mark.unit
    def test_adds_new_attribute(self, attribute_token):
        # Arrange
        element = Token(
            type="attribute",
            tag="",
            nesting=0,
            children=[attribute_token("attribute_name")],
        )
        object_stack = [{"attributes": []}]

        # Act
        process_attribute(element, object_stack)

        # Assert
        assert len(object_stack[-1]["attributes"]) == 1
        assert object_stack[-1]["attributes"][0]["name"] == "attribute_name"

    # Sets the attribute name to the content of the first text element in the children of the element.
    @pytest.mark.unit
    def test_sets_attribute_name(self, attribute_token):
        # Arrange
        element = Token(
            type="attribute",
            tag="",
            nesting=0,
            children=[attribute_token("attribute_name")],
        )
        object_stack = [{"attributes": []}]

        # Act
        process_attribute(element, object_stack)

        # Assert
        assert object_stack[-1]["attributes"][0]["name"] == "attribute_name"

    # Sets the attribute required value to True if the element contains a strong tag.
    @pytest.mark.unit
    def test_sets_attribute_required_true(self, required_token):
        # Arrange
        element = Token(
            type="attribute",
            tag="",
            nesting=0,
            children=[required_token],
        )
        object_stack = [{"attributes": []}]

        # Act
        process_attribute(element, object_stack)

        # Assert
        assert object_stack[-1]["attributes"][0]["required"] is True

    # Raises a ValueError if the element has no children.
    @pytest.mark.unit
    def test_raises_value_error_no_children(self):
        # Arrange
        element = Token(
            tag="",
            nesting=0,
            type="attribute",
            children=[],
        )
        object_stack = [{"attributes": []}]

        # Act & Assert
        with pytest.raises(AssertionError):
            process_attribute(element, object_stack)

    # Raises a ValueError if no attribute name is found in the children of the element.
    @pytest.mark.unit
    def test_raises_value_error_no_attribute_name(self, empty_attribute_token):
        # Arrange
        element = Token(
            tag="",
            nesting=0,
            type="attribute",
            children=[empty_attribute_token],
        )
        object_stack = [{"attributes": []}]

        # Act & Assert
        with pytest.raises(ValueError):
            process_attribute(element, object_stack)

    # Sets the attribute default value to None if the element does not contain a strong tag.
    @pytest.mark.unit
    def test_sets_attribute_default_none(self, attribute_token):
        # Arrange
        element = Token(
            tag="",
            nesting=0,
            type="attribute",
            children=[attribute_token("attribute_name")],
        )
        object_stack = [{"attributes": []}]

        # Act
        process_attribute(element, object_stack)

        # Assert
        assert object_stack[-1]["attributes"][0]["default"] is None


class TestGetParent:
    # Returns the parent of an object with a single text child
    @pytest.mark.unit
    def test_returns_parent_single_text_child(self):
        children = [Token(type="text", level=1, content="parent", tag="", nesting=0)]
        assert get_parent(children) == "parent"

    # Returns the parent of an object with multiple children, where the first child is a text element with level 1
    @pytest.mark.unit
    def test_returns_parent_multiple_children_level_1(self):
        children = [
            Token(type="text", tag=None, nesting=None, level=1, content="parent"),
            Token(type="text", tag=None, nesting=None, level=2, content="child1"),
            Token(type="text", tag=None, nesting=None, level=2, content="child2"),
        ]
        assert get_parent(children) == "parent"

    # Raises an exception if no text element with level 1 is found
    @pytest.mark.unit
    def test_raises_exception_no_level_1_text_element(self):
        children = [
            Token(type="text", tag="", nesting=0, level=2, content="child1"),
            Token(type="text", tag="", nesting=0, level=2, content="child2"),
        ]
        with pytest.raises(StopIteration):
            get_parent(children)

    # Raises an exception if no children are found
    @pytest.mark.unit
    def test_raises_exception_no_children(self):
        children = []
        with pytest.raises(StopIteration):
            get_parent(children)

    # Raises an exception if children is None
    @pytest.mark.unit
    def test_raises_exception_children_none(self):
        children = None
        with pytest.raises(TypeError):
            get_parent(children)


class TestHasParent:
    # Returns True if any element in the list of children has a level of 1
    @pytest.mark.unit
    def test_returns_true_if_any_element_has_level_1(self):
        # Arrange
        children = [
            Token("type", "tag", 0),
            Token("type", "tag", 1),
            Token("type", "tag", 2),
            Token("type", "tag", 1),
        ]

        # Act
        result = has_parent(children)

        # Assert
        assert result is False

    # Returns False if none of the elements in the list of children have a level of 1
    @pytest.mark.unit
    def test_returns_false_if_none_of_the_elements_have_level_1(self):
        # Arrange
        children = [
            Token(type="", tag="", nesting=0, level=0),
            Token(type="", tag="", nesting=0, level=2),
            Token(type="", tag="", nesting=0, level=3),
        ]

        # Act
        result = has_parent(children)

        # Assert
        assert result is False

    # Returns False if children is an empty list
    @pytest.mark.unit
    def test_returns_false_if_children_is_empty_list(self):
        # Arrange
        children = []

        # Act
        result = has_parent(children)

        # Assert
        assert result is False

    # Returns False if children is None
    @pytest.mark.unit
    def test_returns_false_if_children_is_none(self):
        # Arrange
        children = []

        # Act
        result = has_parent(children)

        # Assert
        assert result is False

    # Returns True if only one element in the list of children has a level of 1
    @pytest.mark.unit
    def test_returns_true_if_only_one_element_has_level_1(self):
        # Arrange
        children = [
            Token("type", "tag", 0),
            Token("type", "tag", 1),
            Token("type", "tag", 2),
            Token("type", "tag", 3),
        ]
        children[1].level = 1  # Set the level attribute of the second element to 1

        # Act
        result = has_parent(children)

        # Assert
        assert result is True

    # Returns True if multiple elements in the list of children have a level of 1
    @pytest.mark.unit
    def test_returns_true_if_multiple_elements_have_level_1(self):
        # Arrange
        children = [
            Token(type="", tag="", nesting=0, level=0),
            Token(type="", tag="", nesting=0, level=1),
            Token(type="", tag="", nesting=0, level=2),
            Token(type="", tag="", nesting=0, level=1),
        ]

        # Act
        result = has_parent(children)

        # Assert
        assert result is True


class TestHasParent:
    # Returns True if the list of children contains a Token with level 1
    @pytest.mark.unit
    def test_returns_true_if_list_contains_token_with_level_1(self):
        children = [
            Token(type="", tag="", nesting=0, level=0),
            Token(type="", tag="", nesting=0, level=1),
            Token(type="", tag="", nesting=0, level=2),
        ]
        assert has_parent(children) is True

    # Returns False if the list of children does not contain a Token with level 1
    @pytest.mark.unit
    def test_returns_false_if_list_does_not_contain_token_with_level_1(self):
        children = [
            Token(type="type", tag="tag", level=0, nesting=0),
            Token(type="type", tag="tag", level=2, nesting=0),
            Token(type="type", tag="tag", level=3, nesting=0),
        ]
        assert has_parent(children) is False

    # Works correctly with a list of children containing only one Token with level 1
    @pytest.mark.unit
    def test_works_correctly_with_list_containing_only_one_token_with_level_1(self):
        children = [Token(type="type", tag="tag", level=1, nesting=0)]
        assert has_parent(children) is True

    # Raises a ValueError if the list of children contains more than one Token with level 1
    @pytest.mark.unit
    def test_raises_value_error_if_list_contains_more_than_one_token_with_level_1(self):
        children = [
            Token(type="", tag="", nesting=0, level=1),
            Token(type="", tag="", nesting=0, level=1),
        ]
        with pytest.raises(ValueError):
            has_parent(children)


class TestGetObjectName:
    # Returns the name of the object when given a list of Tokens containing at least one child element.
    @pytest.mark.unit
    def test_returns_name_with_children(self):
        children = [Token(type="type", tag="tag", nesting=0, content="[Object]")]
        assert get_object_name(children=children) == "Object"

    # Returns the name of the object with leading and trailing whitespaces removed.
    @pytest.mark.unit
    def test_returns_name_with_whitespace_removed(self):
        children = [Token(type="type", tag="tag", nesting=0, content="[   Object   ]")]
        assert get_object_name(children=children) == "Object"

    # Returns the name of the object with square brackets removed.
    @pytest.mark.unit
    def test_returns_name_with_square_brackets_removed(self):
        children = [Token(type="type", tag="tag", nesting=0, content="[Object]")]
        assert get_object_name(children=children) == "Object"

    # Raises an IndexError when given an empty list of Tokens.
    @pytest.mark.unit
    def test_raises_index_error_with_empty_list(self):
        children = []
        with pytest.raises(IndexError):
            get_object_name(children=children)

    # Returns an empty string when the first child element has no content.
    @pytest.mark.unit
    def test_returns_empty_string_with_no_content(self):
        children = [Token(type="", tag="", nesting=0, content="")]
        assert get_object_name(children=children) == ""

    # Returns the object name when the first child element has no type.
    @pytest.mark.unit
    def test_returns_object_name_with_no_type(self):
        children = [Token(tag="", nesting=0, content="[Object]", type=None)]
        assert get_object_name(children=children) == "Object"


class TestGatherObjectsToKeep:
    # Should return a list containing the name of the object and its parent if it exists
    @pytest.mark.unit
    def test_object_with_parent(self):
        objs = [
            {"name": "parent", "attributes": []},
            {"name": "child", "parent": "parent", "attributes": []},
        ]
        result = gather_objects_to_keep("child", objs)
        assert result == ["child", "parent"]

    # Should return a list containing only the name of the object if it has no parent
    @pytest.mark.unit
    def test_object_without_parent(self):
        objs = [
            {"name": "object1", "attributes": []},
            {"name": "object2", "attributes": []},
            {"name": "object3", "attributes": []},
        ]
        result = gather_objects_to_keep("object2", objs)
        assert result == ["object2"]

    # Should return an empty list if the object is not found in the list of objects
    @pytest.mark.unit
    def test_object_not_found(self):
        objs = [{"name": "object1"}, {"name": "object2"}, {"name": "object3"}]
        result = gather_objects_to_keep("object4", objs)
        assert result is None

    # Should handle circular references in the data model without going into an infinite loop
    @pytest.mark.unit
    def test_circular_references_fixed(self):
        objs = [
            {"name": "object1", "parent": "object2", "attributes": []},
            {"name": "object2", "parent": "object1", "attributes": []},
        ]
        result = gather_objects_to_keep("object1", objs)
        assert result == ["object1", "object2"]

    # Should handle objects with missing or invalid attributes without raising an exception
    @pytest.mark.unit
    def test_missing_attributes_fixed(self):
        objs = [
            {"name": "object1", "parent": "object2", "attributes": []},
            {"name": "object2", "parent": "object3", "attributes": []},
            {"name": "object3", "attributes": [{"type": ["attribute1"]}]},
            {"name": "object4", "attributes": [{"type": ["attribute2"]}]},
        ]
        result = gather_objects_to_keep("object1", objs)
        assert result == ["object1", "object2"]

    # Should handle empty list of objects without raising an exception
    @pytest.mark.unit
    def test_empty_list_of_objects(self):
        objs = []
        result = gather_objects_to_keep("object1", objs)
        assert result is None


class TestProcessObject:
    # Adds a new object to the object stack with name, attributes, type, and subtypes.
    @pytest.mark.unit
    def test_adds_new_object(self):
        element = Token(
            type="object",
            tag="",
            nesting=0,
            children=[
                Token(type="text", tag="", nesting=0, content="[Object]"),
                Token(type="text", tag="", nesting=0, content="Object description"),
            ],
        )
        object_stack = []
        process_object(element, object_stack)
        assert len(object_stack) == 1
        assert object_stack[0]["name"] == "Object"
        assert object_stack[0]["attributes"] == []
        assert object_stack[0]["type"] == "object"
        assert object_stack[0]["subtypes"] == []

    # Sets the parent of the object if it has one.
    @pytest.mark.unit
    def test_sets_parent_if_exists(self):
        element = Token(
            type="object",
            tag="",
            nesting=0,
            children=[
                Token(type="text", tag="", nesting=0, content="[Object]"),
                Token(type="text", tag="", nesting=0, content="Object description"),
                Token(type="text", tag="", nesting=0, content="[Parent]"),
            ],
        )
        object_stack = []
        process_object(element, object_stack)
        assert len(object_stack) == 1
        assert object_stack[0]["name"] == "Object"
        assert object_stack[0]["attributes"] == []
        assert object_stack[0]["type"] == "object"
        assert object_stack[0]["subtypes"] == []
        if "parent" in object_stack[0]:
            assert object_stack[0]["parent"] == "Parent"

    # Raises an IndexError if the object has no children.
    @pytest.mark.unit
    def test_raises_index_error_if_no_children(self):
        element = Token(type="object", tag="", nesting=0, children=[])
        object_stack = []
        with pytest.raises(IndexError):
            process_object(element, object_stack)

    # None.
    @pytest.mark.unit
    def test_no_behaviour_with_child(self):
        element = Token(
            type="object",
            tag="",
            nesting=0,
            children=[Token(type="text", tag="", nesting=0, content="object_name")],
        )
        object_stack = []
        process_object(element, object_stack)
        assert len(object_stack) == 1
        assert object_stack[0]["name"] == "object_name"
        assert object_stack[0]["docstring"] == ""
        assert object_stack[0]["attributes"] == []
        assert object_stack[0]["type"] == "object"
        assert object_stack[0]["subtypes"] == []


class TestAddModuleNameToObjects:
    # The function correctly adds the module name to each object in the object stack.
    @pytest.mark.unit
    def test_add_module_name_to_objects_correctly_adds_module_name(self):
        # Arrange
        name = "test_module"
        object_stack = [{"key": "value"}, {"key": "value"}]

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        for obj in result:
            assert obj["module"] == name

    # The function returns the modified object stack.
    @pytest.mark.unit
    def test_add_module_name_to_objects_returns_modified_object_stack(self):
        # Arrange
        name = "test_module"
        object_stack = [{"key": "value"}, {"key": "value"}]

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        assert result == object_stack

    # The function handles an empty object stack gracefully and returns an empty list.
    @pytest.mark.unit
    def test_add_module_name_to_objects_handles_empty_object_stack(self):
        # Arrange
        name = "test_module"
        object_stack = []

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        assert result == []

    # The name argument is an empty string.
    @pytest.mark.unit
    def test_add_module_name_to_objects_with_empty_string_name(self):
        # Arrange
        name = ""
        object_stack = [{"key": "value"}, {"key": "value"}]

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        for obj in result:
            assert obj["module"] == name

    # The name argument is None.
    @pytest.mark.unit
    def test_add_module_name_to_objects_with_none_name(self):
        # Arrange
        name = None
        object_stack = [{"key": "value"}, {"key": "value"}]

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        for obj in result:
            assert obj["module"] == name

    # The object stack contains an object with no keys.
    @pytest.mark.unit
    def test_add_module_name_to_objects_with_object_stack_containing_object_with_no_keys(
        self,
    ):
        # Arrange
        name = "test_module"
        object_stack = [{"key": "value"}, {}, {"key": "value"}]

        # Act
        result = add_module_name_to_objects(name, object_stack)

        # Assert
        for obj in result:
            assert obj["module"] == name


class TestCheckPreviousAttribute:
    # The function should not raise any error if the object stack is empty.
    @pytest.mark.unit
    def test_empty_object_stack(self):
        object_stack = []
        try:
            check_previous_attribute(object_stack)
        except ValueError:
            pytest.fail("Unexpected ValueError raised")

    # The function should not raise any error if the last object in the stack has no attributes.
    @pytest.mark.unit
    def test_last_object_no_attributes(self):
        object_stack = [{"attributes": []}]
        try:
            check_previous_attribute(object_stack)
        except ValueError:
            pytest.fail("Unexpected ValueError raised")

    # The function should not raise any error if the last attribute in the last object has a 'type' key.
    @pytest.mark.unit
    def test_last_attribute_with_type_key(self):
        object_stack = [{"attributes": [{"type": "int"}]}]
        try:
            check_previous_attribute(object_stack)
        except ValueError:
            pytest.fail("Unexpected ValueError raised")

    # The function should raise a ValueError if the last attribute in the last object has no 'type' key.
    @pytest.mark.unit
    def test_last_attribute_without_type_key(self):
        object_stack = [{"attributes": [{"name": "attr"}]}]
        with pytest.raises(ValueError):
            check_previous_attribute(object_stack)

    # The function should raise a ValueError if the object stack has more than one object and the last attribute of the second to last object has no 'type' key, and the last object has attributes and the last attribute also has no 'type' key.
    @pytest.mark.unit
    def test_multiple_objects_last_attribute_without_type_key(self):
        object_stack = [
            {"attributes": [{"type": "int"}]},
            {"attributes": [{"name": "attr"}]},
        ]
        with pytest.raises(ValueError):
            check_previous_attribute(object_stack)
