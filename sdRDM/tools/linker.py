from copy import deepcopy
from typing import Any, Dict, Tuple, get_origin

import validators
from dotted_dict import DottedDict


class Linker:
    def __init__(self, template: Dict):
        assert (
            "__model__" in template
        ), "Mapping template must contain a '__model__' key."

        assert (
            "__sources__" in template
        ), "Mapping template must contain a '__sources__' key."

        self.template = deepcopy(template)
        self.__sources__ = self._build_sources(self.template.pop("__sources__"))
        self.__model__ = self.template.pop("__model__")

    def _build_sources(self, sources: Dict[str, str]):
        """
        Build sources based on the provided dictionary.

        Args:
            sources (Dict[str, str]): A dictionary containing class names as keys and resource URLs or local paths as values.

        Returns:
            DottedDict: A DottedDict object containing the built sources.

        Raises:
            ValueError: If the resource type is not supported.
            AssertionError: If the library does not contain the specified class name.
        """
        built_sources = {}
        for cls_name, resource in sources.items():
            if validators.url(resource) and "github.com" in resource:
                lib = self._build_github_lib(resource)
            elif not validators.url(resource):
                lib = self._build_local_lib(resource)
            else:
                raise ValueError(
                    f"Unsupported resource type '{resource}'. Only GitHub repositories and local markdown files are supported."
                )

            assert hasattr(
                lib, cls_name
            ), f"Library does not contain class '{cls_name}'."

            built_sources[cls_name] = getattr(lib, cls_name)

        return built_sources

    @staticmethod
    def _build_github_lib(url: str):
        """
        Builds a GitHub library from the given URL.

        Args:
            url (str): The URL of the GitHub repository.

        Returns:
            DataModel: The built GitHub library.
        """
        from sdRDM import DataModel

        if "@" in url:
            repo, branch = url.split("@")
        else:
            repo = url
            branch = None

        return DataModel.from_git(
            url=repo,
            tag=branch,
        )

    @staticmethod
    def _build_local_lib(path: str):
        """
        Builds a local library from a markdown file.

        Args:
            path (str): The path to the markdown file.

        Returns:
            DataModel: The constructed DataModel object.
        """
        from sdRDM import DataModel

        return DataModel.from_markdown(path)

    def __call__(
        self,
        source: "DataModel",
        target: "DataModel",
    ) -> Any:
        """
        Maps attributes from the source DataModel to the target DataModel based on the specified mapping template.

        Args:
            source (DataModel): The source DataModel object.
            target (DataModel): The target DataModel object.

        Returns:
            Any: The mapped objects as a DottedDict.
        """

        self._validate(source, target)

        src_meta = source._meta_path()
        trgt_meta = target._meta_path()

        if src_meta not in self.template:
            return None

        mapping = self.template[src_meta]
        obj_mappings = self._map_attributes(
            source,
            mapping,
            trgt_meta,
        )

        mapped_objects = {}

        for dtype, attributes in obj_mappings.items():
            if dtype not in target._types:
                raise ValueError(
                    f"Target object does not contain attribute '{dtype}', but has been specified as a target in the mapping."
                )

            self._convert(
                target=target,
                dtype=dtype,
                attributes=attributes,
                mapped_objects=mapped_objects,
            )

        return DottedDict(mapped_objects)

    def _validate(
        self,
        source: "DataModel",
        target: "DataModel",
    ) -> None:
        """
        Validates the source and target parameters.

        Args:
            source (DataModel): The source parameter to be validated.
            target (DataModel): The target parameter to be validated.

        Raises:
            AssertionError: If the source parameter is not an instance of DataModel.
            AssertionError: If the target parameter is not an instance of DataModel.
        """

        from sdRDM import DataModel

        assert isinstance(
            source, DataModel
        ), f"Source must be a subclass of DataModel, not {type(source).__name__}"

        assert isinstance(
            target, DataModel
        ), f"Target must be a subclass of DataModel, not {type(source).__name__}"

    def _map_attributes(
        self,
        obj: "DataModel",
        mapping: Dict,
        trgt_meta: str,
    ) -> Dict:
        """
        Maps attributes from the source object to the target object based on the provided mapping.

        Args:
            obj (DataModel): The source object from which attributes will be mapped.
            mapping (Dict): A dictionary containing the mapping of source attributes to target paths.
            trgt_meta (str): The target metadata to filter the mapping.

        Returns:
            Dict: A dictionary containing the mapped attributes of the target object.
        """
        attribute_mappings = {}

        for src_attr, tgrt_path in mapping.items():
            if trgt_meta not in tgrt_path:
                continue

            trgt_obj, trgt_attr = self._split_path_to_obj_attr(tgrt_path)

            if trgt_obj not in attribute_mappings:
                attribute_mappings[trgt_obj] = {}

            attribute_mappings[trgt_obj][trgt_attr] = getattr(obj, src_attr)

        return attribute_mappings

    @staticmethod
    def _split_path_to_obj_attr(path: str) -> Tuple[str, str]:
        """
        Splits the given path into object and attribute.

        Args:
            path (str): The path to be split.

        Returns:
            Tuple[str, str]: A tuple containing the object and attribute.
        """
        *_, obj, attr = path.split("/")

        return obj, attr

    @staticmethod
    def _is_multiple(
        obj: "DataModel",
        attr: str,
    ) -> bool:
        """
        Checks if the given attribute is a multiple.

        Args:
            obj (DataModel): The object to check.
            attr (str): The attribute to check.

        Returns:
            bool: True if the attribute is a multiple, False otherwise.
        """
        return get_origin(obj.model_fields[attr].annotation) is list

    def _convert(
        self,
        target: "DataModel",
        dtype: str,
        attributes: Dict,
        mapped_objects: Dict,
    ) -> None:
        """
        Converts the given attributes into a mapped object of the specified data type and assigns it to the target object.

        Args:
            target (DataModel): The target object to which the mapped object will be assigned.
            dtype (str): The data type of the mapped object.
            attributes (Dict): The attributes of the mapped object.
            mapped_objects (Dict): A dictionary to store the mapped objects.

        Returns:
            None
        """
        is_multiple = self._is_multiple(target, dtype)
        mapped_obj = target._types[dtype][0](**attributes)

        if is_multiple:
            getattr(target, dtype).append(mapped_obj)
            mapped_objects[dtype] = getattr(target, dtype)[-1]
        else:
            mapped_obj._parent = target
            mapped_obj._attribute = dtype

            setattr(target, dtype, mapped_obj)
            mapped_objects[dtype] = getattr(target, dtype)
