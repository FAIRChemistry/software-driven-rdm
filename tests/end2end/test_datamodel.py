from sdRDM import DataModel


class TestGetMethod:

    def test_get_method_by_meta_with_zeros(self, model_all):
        """Tests whether the get_method_by_meta method returns the correct values"""

        # Arrange
        dataset = model_all.Root(
            multiple_primitives=[0.0, 2.0],
            nested_multiple_obj=[
                model_all.Nested(float_value=0.0),
                model_all.Nested(float_value=2.0),
            ],
        )

        # Act
        multiple_primitives = dataset.get("multiple_primitives")
        nested_multiple_obj = dataset.get("nested_multiple_obj")
        nested_multiple_obj_floats = dataset.get("nested_multiple_obj/float_value")

        assert multiple_primitives == [[0.0, 2.0]]
        assert all(isinstance(obj, model_all.Nested) for obj in nested_multiple_obj[0])
        assert all(obj.float_value in [0.0, 2.0] for obj in nested_multiple_obj[0])
        assert nested_multiple_obj_floats == [0.0, 2.0]
