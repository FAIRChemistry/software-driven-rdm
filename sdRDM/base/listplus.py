from typing import Any, Callable, List, Union


class ListPlus(List[Any]):
    """
    This class extends a list to a search functionality
    similar to a dictionary, but based on its available
    attributes.
    """

    __parent__: "DataModel"
    __types__: List["DataModel"]
    __attribute__: str

    def __init__(self, *args, **kwargs):
        super(ListPlus, self).__init__()

        self.__parent__ = None
        self.__attribute__ = None

        for arg in args:
            if "generator object" in repr(arg):
                for element in list(arg):
                    self.append(element)
            else:
                self.append(arg)

    def append(self, *args):
        for arg in args:
            if hasattr(arg, "__fields__") and self.is_part_of_model():
                arg.__parent__ = self.__parent__
                arg._check_references(self.__attribute__, arg)

            super().append(arg)

    def is_part_of_model(self) -> bool:
        """Checks whether this list is already integrated"""
        return self.__parent__ is not None and self.__attribute__ is not None

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "__parent__" and value is not None:
            self.set_parent_for_object_entries(value)

        return super().__setattr__(name, value)

    def set_parent_for_object_entries(self, parent):
        """Adds parent relation so object entries once it has been set"""
        for entry in self:
            if not hasattr(entry, "__fields__"):
                continue

            entry.__parent__ = parent

    def get(self, query: Callable, attr: str = "id"):
        """Given an a query, returns all objects that match

        Adding an attribute allows to scan classes too, if
        the list is made of classes. The 'attr' argument
        allows to specify for which attribute to filter.
        Defaults to ID.

        """

        if not all([self._is_builtin(obj) for obj in self]):
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
