from typing import Any, Callable, List, Optional, Union


class ListPlus(List[Any]):
    """
    This class extends a list to a search functionality
    similar to a dictionary, but based on its available
    attributes.
    """

    _parent: "DataModel"
    __types__: List["DataModel"]
    _attribute: Optional[str]

    def __init__(self, *args, **kwargs):
        super(ListPlus, self).__init__()

        self._parent = None
        self._attribute = None

        for arg in args:
            if "generator object" in repr(arg):
                for element in list(arg):
                    self.append(element)
            else:
                self.append(arg)

    def append(self, *args):
        for arg in args:
            if hasattr(arg, "model_fields") and self.is_part_of_model():
                arg._parent = self._parent
                arg._attribute = self._attribute
                arg._check_references(self._attribute, arg)

            super().append(arg)

    def is_part_of_model(self) -> bool:
        """Checks whether this list is already integrated"""
        return self._parent is not None

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_parent" and value is not None:
            self.set_parent_for_object_entries(value)
        elif name == "_attribute" and value is not None:
            self.set_attribute_for_object_entries(value)
        elif hasattr(value, "model_fields") and self._parent is not None:
            value._parent = self._parent
            value._attribute = self._attribute

        return super().__setattr__(name, value)

    def set_parent_for_object_entries(self, parent):
        """Adds parent relation so object entries once it has been set"""
        for entry in self:
            if not hasattr(entry, "model_fields"):
                continue

            entry._parent = parent

    def set_attribute_for_object_entries(self, attribute):
        """Adds attribute relation so object entries once it has been set"""
        for entry in self:
            if not hasattr(entry, "model_fields"):
                continue

            entry._attribute = attribute

    def get(
        self,
        query: Union[Callable, str, None] = None,
        attr: str = "id",
        path: Optional[str] = None,
    ):
        """Given an a query, returns all objects that match

        Adding an attribute allows to scan classes too, if
        the list is made of classes. The 'attr' argument
        allows to specify for which attribute to filter.
        Defaults to ID.

        """

        is_only_builtin = all(self._is_builtin(obj) for obj in self)

        if isinstance(query, str):
            query = lambda x: x == query

        if path and attr and not is_only_builtin:
            l = ListPlus()

            for value in self:
                l += value.get(path)

            return l

        if not is_only_builtin:
            # Check for objects
            search_fun = lambda obj: query(obj.__dict__[attr])
        else:
            raise TypeError(
                f"Mixed types in list, can only search homogeneous (builtin or classes)."
            )

        return list(filter(search_fun, self))

    @staticmethod
    def _is_builtin(obj):
        return obj.__class__.__module__ == "builtins"
