from typing import Any, List


class ListPlus(List[Any]):
    """
    This class extends a list to a search functionality
    similar to a dictionary, but based on its available
    attributes.
    """

    def __init__(self, *args, in_setup: bool = True, **kwargs):
        super(ListPlus, self).__init__()

        for arg in args:
            if "generator object" in repr(arg):
                for element in list(arg):
                    self.append(element)
            else:
                self.append(arg)

    def append(self, *args):
        for arg in args:
            super().append(arg)

    def get(self, query: str, attr: str = "id"):
        """Given an a query, returns all objects that match

        Adding an attribute allows to scan classes too, if
        the list is made of classes. The 'attr' argument
        allows to specify for which attribute to filter.
        Defaults to ID.

        """

        if not all([self._is_builtin(obj) for obj in self]):
            # Check for objects
            search_fun = lambda obj: obj.__dict__[attr] == query
        elif all([self._is_builtin(obj) for obj in self]):
            # Check for builtins
            search_fun = lambda elem: elem == query
        else:
            raise TypeError(
                f"Mixed types in list, can only search homogeneous (builtin or classes)."
            )

        return list(filter(search_fun, self))

    @staticmethod
    def _is_builtin(obj):
        return obj.__class__.__module__ == "builtins"
