import pytest

from markdown_it.token import Token
from sdRDM.markdown.markdownparser import MarkdownParser


class TestMarkdownParser:
    # Parses a given markdown file to a mermaid schema from which code is generated
    @pytest.mark.unit
    def test_parse_markdown_file(self):
        # Arrange
        markdown_file = open("tests/fixtures/static/model_minimal.md", "r")

        # Act
        parser = MarkdownParser.parse(markdown_file)

        # Assert
        assert len(parser.objects) == 3
        assert len(parser.enums) == 1
        assert len(parser.inherits) == 1
        assert len(parser.compositions) == 2
        assert len(parser.external_objects) == 0
        assert isinstance(parser, MarkdownParser)
        markdown_file.close()

    # Adds another parser to the current one
    @pytest.mark.unit
    def test_add_parser(self):
        # Arrange
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()

        # Add objects, enums, inherits, compositions, and external_objects to both parsers
        parser1.objects = [
            {"name": "object1"},
            {"name": "object2"},
        ]
        parser2.objects = [
            {"name": "object3"},
            {"name": "object4"},
        ]
        parser1.enums = [
            {"name": "enum1"},
            {"name": "enum2"},
        ]
        parser2.enums = [
            {"name": "enum3"},
            {"name": "enum4"},
        ]
        parser1.inherits = [
            {"parent": "parent1", "child": "child1"},
            {"parent": "parent2", "child": "child2"},
        ]
        parser2.inherits = [
            {"parent": "parent3", "child": "child3"},
            {"parent": "parent4", "child": "child4"},
        ]
        parser1.compositions = [
            {"container": "container1", "module": "module1"},
            {"container": "container2", "module": "module2"},
        ]
        parser2.compositions = [
            {"container": "container3", "module": "module3"},
            {"container": "container4", "module": "module4"},
        ]
        parser1.external_objects = {
            "external1": {
                "objects": [{"name": "external_object1"}, {"name": "external_object2"}]
            }
        }
        parser2.external_objects = {
            "external2": {
                "objects": [
                    {"name": "external_object3"},
                    {"name": "external_object4"},
                ]
            }
        }

        # Act
        parser1.add_model(parser2)

        # Assert
        assert len(parser1.objects) == 4
        assert len(parser1.enums) == 4
        assert len(parser1.inherits) == 4
        assert len(parser1.compositions) == 4
        assert len(parser1.external_objects) == 2

    # Raises an AssertionError if the given remote model has redundant object names
    @pytest.mark.unit
    def test_add_model_with_duplicate_object_names(self):
        # Arrange
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()
        parser2.objects = [{"name": "Object1"}, {"name": "Object2"}]
        parser1.objects = [{"name": "Object2"}]  # Set duplicate object name

        # Act and Assert
        with pytest.raises(AssertionError):
            parser1.add_model(parser2)


class Test_HasDuplicateObjectNames:
    # Returns an empty set when there are no duplicate object names between self and parser.
    @pytest.mark.unit
    def test_no_duplicate_object_names(self):
        # Initialize the MarkdownParser objects
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()

        # Set the objects attribute for both parsers
        parser1.objects = [
            {"name": "Object1", "type": "Type1"},
            {"name": "Object2", "type": "Type2"},
            {"name": "Object3", "type": "Type3"},
        ]
        parser2.objects = [
            {"name": "Object4", "type": "Type4"},
            {"name": "Object5", "type": "Type5"},
            {"name": "Object6", "type": "Type6"},
        ]

        # Invoke the _has_duplicate_object_names method on parser1
        duplicate_objects = parser1._has_duplicate_object_names(parser2)

        # Assert that the duplicate_objects set is empty
        assert duplicate_objects == set()

    # Returns an empty set when self and parser have no objects.
    @pytest.mark.unit
    def test_no_objects(self):
        # Initialize the MarkdownParser objects
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()

        # Invoke the _has_duplicate_object_names method on parser1
        duplicate_objects = parser1._has_duplicate_object_names(parser2)

        # Assert that the duplicate_objects set is empty
        assert duplicate_objects == set()

    # Returns an empty set when parser has no objects.
    @pytest.mark.unit
    def test_parser_no_objects(self):
        # Initialize the MarkdownParser objects
        parser1 = MarkdownParser()
        parser2 = MarkdownParser()

        # Set the objects attribute for parser1
        parser1.objects = [
            {"name": "Object1", "type": "Type1"},
            {"name": "Object2", "type": "Type2"},
            {"name": "Object3", "type": "Type3"},
        ]

        # Invoke the _has_duplicate_object_names method on parser1
        duplicate_objects = parser1._has_duplicate_object_names(parser2)

        # Assert that the duplicate_objects set is empty
        assert duplicate_objects == set()


class TestMergeExternalObjects:
    # Merges all external objects into the current parser when there are no duplicates.
    @pytest.mark.unit
    def test_merge_external_objects_no_duplicates(self):
        external_objects = {
            "external_parser1": MarkdownParser(),
            "external_parser2": MarkdownParser(),
            "external_parser3": MarkdownParser(),
        }

        parser = MarkdownParser()
        parser.external_objects = external_objects

        parser.merge_external_objects()

        assert len(parser.objects) == 0
        assert len(parser.enums) == 0
        assert len(parser.inherits) == 0
        assert len(parser.compositions) == 0
        assert len(parser.external_objects) == 3
        assert parser.external_objects == external_objects

    # Merges external objects without duplicate names by appending them to the current parser.
    @pytest.mark.unit
    def test_merge_external_objects_without_duplicates(self):
        external_objects = {
            "external_parser1": MarkdownParser(),
            "external_parser2": MarkdownParser(),
            "external_parser3": MarkdownParser(),
        }

        parser = MarkdownParser()
        parser.external_objects = external_objects

        # Add unique object names
        external_objects["external_parser1"].objects = [
            {"name": "object1"},
            {"name": "object2"},
        ]
        external_objects["external_parser2"].objects = [
            {"name": "object4"},
            {"name": "object3"},
        ]

        parser.merge_external_objects()

        assert len(parser.objects) == 4
        assert len(parser.enums) == 0
        assert len(parser.inherits) == 0
        assert len(parser.compositions) == 0
        assert len(parser.external_objects) == 3
        assert parser.external_objects == external_objects

    # Raises an AssertionError when attempting to merge a non-MarkdownParser object.
    @pytest.mark.unit
    def test_merge_external_objects_non_markdown_parser(self):
        external_objects = {
            "external_parser1": MarkdownParser(),
            "external_parser2": MarkdownParser(),
            "external_parser3": MarkdownParser(),
        }

        parser = MarkdownParser()
        parser.external_objects = external_objects

        # Add non-MarkdownParser object
        external_objects["external_parser1"] = "not a MarkdownParser object"

        with pytest.raises(AssertionError):
            parser.merge_external_objects()

    # Raises an AssertionError when attempting to merge an external object with duplicate object names.
    @pytest.mark.unit
    def test_merge_external_objects_duplicate_object_names(self):
        external_objects = {
            "external_parser1": MarkdownParser(),
            "external_parser2": MarkdownParser(),
            "external_parser3": MarkdownParser(),
        }

        parser = MarkdownParser()
        parser.external_objects = external_objects

        # Add duplicate object names
        external_objects["external_parser1"].objects = [
            {"name": "object1"},
            {"name": "object2"},
        ]
        external_objects["external_parser2"].objects = [
            {"name": "object2"},
            {"name": "object3"},
        ]
        external_objects["external_parser3"].objects = [
            {"name": "object3"},
            {"name": "object4"},
        ]

        with pytest.raises(AssertionError):
            parser.merge_external_objects()

    # Merges an empty external object into the current parser without raising an error.
    @pytest.mark.unit
    def test_merge_external_objects_empty_external_object(self):
        external_objects = {
            "external_parser1": MarkdownParser(),
            "external_parser2": MarkdownParser(),
            "external_parser3": MarkdownParser(),
        }

        parser = MarkdownParser()
        parser.external_objects = external_objects

        # Add empty external object
        external_objects["external_parser1"].objects = []

        parser.merge_external_objects()

        assert len(parser.objects) == 0
        assert len(parser.enums) == 0
        assert len(parser.inherits) == 0
        assert len(parser.compositions) == 0
        assert len(parser.external_objects) == 3
        assert parser.external_objects == external_objects


class TestGetH2Indices:
    # Returns a list of tuples containing the name of the H2 heading and its index in the document when given a list of tokens representing a markdown document with H2 headings.
    @pytest.mark.unit
    def test_h2_indices_with_h2_headings(self):
        doc = [
            Token(tag="h1", type="heading_open", nesting=1),
            Token(content="Title", tag="h1", type="heading_close", nesting=-1),
            Token(tag="h2", type="heading_open", nesting=1),
            Token(content="Object 1", tag="h2", type="heading_close", nesting=-1),
            Token(tag="p", type="paragraph_open", nesting=1),
            Token(
                content="This is object 1", tag="p", type="paragraph_close", nesting=-1
            ),
            Token(tag="h2", type="heading_open", nesting=1),
            Token(content="Object 2", tag="h2", type="heading_close", nesting=-1),
            Token(tag="p", type="paragraph_open", nesting=1),
            Token(
                content="This is object 2", tag="p", type="paragraph_close", nesting=-1
            ),
            Token(tag="h2", type="heading_open", nesting=1),
            Token(content="Enumerations", tag="h2", type="heading_close", nesting=-1),
            Token(tag="p", type="paragraph_open", nesting=1),
            Token(
                content="This is an enumeration",
                tag="p",
                type="paragraph_close",
                nesting=-1,
            ),
        ]

        parser = MarkdownParser()
        indices = parser.get_h2_indices(doc)
        expected_indices = [
            ("Object 1", 2),
            ("Object 2", 6),
            ("Enumerations", 10),
            ("END", 14),
        ]
        assert indices == expected_indices

    # Returns an empty list when given a list of tokens representing a markdown document without H2 headings.
    @pytest.mark.unit
    def test_h2_indices_without_h2_headings(self):
        doc = [
            Token(tag="h1", type="heading_open", nesting=1),
            Token(content="Title", tag="h1", type="heading_close", nesting=-1),
            Token(tag="p", type="paragraph_open", nesting=1),
            Token(
                content="This is a paragraph",
                tag="p",
                type="paragraph_close",
                nesting=-1,
            ),
        ]

        parser = MarkdownParser()
        indices = parser.get_h2_indices(doc)
        expected_indices = [("END", 4)]
        assert indices == expected_indices

    # Returns a list containing a single tuple with the name "END" and the length of the document when given a list of tokens representing a markdown document with only one H2 heading.
    @pytest.mark.unit
    def test_h2_indices_with_one_h2_heading(self):
        doc = [
            Token(tag="h1", type="heading_open", nesting=1),
            Token(content="Title", tag="h1", type="heading_close", nesting=-1),
            Token(tag="h2", type="heading_open", nesting=1),
            Token(content="Object 1", tag="h2", type="heading_close", nesting=-1),
            Token(tag="p", type="paragraph_open", nesting=1),
            Token(
                content="This is object 1", tag="p", type="paragraph_close", nesting=-1
            ),
        ]

        parser = MarkdownParser()
        indices = parser.get_h2_indices(doc)
        expected_indices = [("Object 1", 2), ("END", 6)]
        assert indices == expected_indices


class TestGetInherits:
    # Appends a dictionary with parent and child keys to inherits list for each object with parent attribute and no duplicates
    @pytest.mark.unit
    def test_append_dictionary_with_parent_and_child_keys(self):
        parser = MarkdownParser()
        parser.objects = [
            {"name": "ChildObject", "parent": "ParentObject"},
            {"name": "AnotherChildObject", "parent": "ParentObject"},
            {"name": "ParentObject"},
            {"name": "GrandchildObject", "parent": "ChildObject"},
        ]

        parser.get_inherits()
        assert parser.inherits == [
            {"parent": "ParentObject", "child": "ChildObject"},
            {"parent": "ParentObject", "child": "AnotherChildObject"},
            {"parent": "ChildObject", "child": "GrandchildObject"},
        ]

    # Returns an empty list when objects is an empty list
    @pytest.mark.unit
    def test_empty_objects_list(self):
        parser = MarkdownParser()
        parser.objects = []

        parser.get_inherits()
        assert parser.inherits == []


class TestGetCompositions:
    # Should handle gracefully when objects list is empty
    @pytest.mark.unit
    def test_empty_objects_list(self):
        parser = MarkdownParser()
        parser.objects = []
        parser.enums = []

        parser.get_compositions()

        assert parser.compositions == []

    # Should correctly identify compositions for objects with nested attributes
    @pytest.mark.unit
    def test_nested_attributes(self):
        parser = MarkdownParser()
        parser.objects = [
            {
                "name": "Object1",
                "attributes": [
                    {"name": "attribute1", "type": ["Type1"]},
                    {"name": "attribute2", "type": ["Type2"]},
                ],
            },
            {"name": "Type1", "attributes": []},
            {"name": "Type2", "attributes": []},
        ]
        parser.enums = []

        parser.get_compositions()

        assert parser.compositions == [
            {"container": "Object1", "module": "Type1"},
            {"container": "Object1", "module": "Type2"},
        ]

    # Should correctly identify compositions for objects with circular dependencies
    @pytest.mark.unit
    def test_circular_dependencies(self):
        parser = MarkdownParser()
        parser.objects = [
            {
                "name": "Object1",
                "attributes": [{"name": "attribute1", "type": ["Type2"]}],
            },
            {
                "name": "Object2",
                "attributes": [{"name": "attribute2", "type": ["Type1"]}],
            },
            {"name": "Type1", "attributes": []},
            {"name": "Type2", "attributes": []},
        ]
        parser.enums = []

        parser.get_compositions()

        assert parser.compositions == [
            {"container": "Object1", "module": "Type2"},
            {"container": "Object2", "module": "Type1"},
        ]

    # Should correctly identify compositions for objects with self-referential attributes
    @pytest.mark.unit
    def test_self_referential_attributes(self):
        parser = MarkdownParser()
        parser.objects = [
            {
                "name": "Object1",
                "attributes": [{"name": "attribute1", "type": ["Object1"]}],
            }
        ]
        parser.enums = []

        parser.get_compositions()

        assert parser.compositions == [{"container": "Object1", "module": "Object1"}]
