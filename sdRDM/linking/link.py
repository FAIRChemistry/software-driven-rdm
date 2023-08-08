import json
import re
import validators
from typing import Dict, List, Tuple

from bigtree import dict_to_tree, levelorder_iter, tree_to_dict
from dotted_dict import DottedDict
from nob import Nob
from pydantic.main import ModelMetaclass


def convert_data_model(dataset, template: Dict = {}):
    """
    Converts a given data model to another model that has been specified
    in the attributes metadata. This will create a new object model from
    the current.

    Example:
        ## Origin
        class DataModel(sdRDM.DataModel):
            foo: str = Field(... another_model="AnotherModel.sub.bar")

        --> The goal is to project the data from 'DataModel' to 'AnotherModel'
            which maps the 'foo' attribute to the nested 'bar' attribute.

    This function provides the utility to map in between data models and
    offer an exchange of data without explicit code.

    Args:
        option (str): Key of the attribute metadata, where the destination is stored.
    """

    # Create target roots and map data
    model = template.pop("__model__")

    if dataset.__class__.__name__ != model:
        raise TypeError(
            f"Linking template requires the source dataset to be of type '{model}' but got '{dataset.__class__.__name__}'"
        )

    sources = {
        root: getattr(_build_source(path), root)
        for root, path in template.pop("__sources__").items()
    }

    return DottedDict(
        {
            name: source(**_assemble_dataset(dataset, template, source)[name])
            for name, source in sources.items()
        }
    )


def _build_source(source: str) -> "DataModel":
    """Builds the source data model from the given template."""

    from sdRDM import DataModel

    if bool(validators.url(source)):
        url, *tag = re.split(r"@|#", source)

        if tag:
            tag = tag[0]
        else:
            tag = None

        return DataModel.from_git(url=url, tag=tag)

    return DataModel.from_markdown(source)


def _assemble_dataset(
    dataset: "DataModel", template: Dict[str, str], target_class: ModelMetaclass
) -> Dict:
    """Creates an explicit mapping from the source to the target dataset and transfers values."""

    target_dataset = {}
    explicit_mapping = _construct_explicit_mapping(dataset, template, target_class)
    for source, target in explicit_mapping.items():
        value = dataset.get(source)

        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        target_dataset[target] = {"value": value}

    return _convert_value_tree_to_dict(dict_to_tree(target_dataset))


def _construct_explicit_mapping(
    dataset: "DataModel", template: Dict[str, str], target_class: ModelMetaclass
):
    """Creates an explicit mapping between the source and target dataset."""

    dataset_paths, source_meta_paths, target_meta_paths = _gather_paths(
        dataset, template, target_class
    )

    explicit_mapping = {}
    for source_path in dataset_paths:
        # Remove digits from path
        source_meta_path = re.sub(r"\/\d+\/", "/", source_path)

        if source_meta_path not in source_meta_paths:
            raise ValueError(f"Path {source_path} not found within the data model")

        target_meta_path = _get_target_meta_path(
            source_meta_paths[source_meta_path], target_meta_paths
        )

        # Adjust indices if necessary
        target_path = _adjust_index(
            target_meta_path, source_path, list(explicit_mapping.values())
        )

        explicit_mapping[source_path] = target_path

    return explicit_mapping


def _gather_paths(
    dataset: "DataModel", template: Dict[str, str], target_class: ModelMetaclass
) -> Tuple[List, Dict, List]:
    """Gathers all the necessary meta and explicit paths.

    Explicit in the sense of strict list indices within the path
    """

    source_meta_paths = _get_source_meta_paths(dataset, template, target_class)
    dataset_paths = [
        str(path)
        for path in dataset.paths()
        if re.sub(r"\/\d+\/", "/", str(path)) in source_meta_paths
    ]

    target_meta_paths = list(tree_to_dict(target_class.meta_tree(show=False)).keys())

    return dataset_paths, source_meta_paths, target_meta_paths


def _get_source_meta_paths(
    dataset: "DataModel", template: Dict[str, Dict], target_class: ModelMetaclass
) -> Dict[str, str]:
    """Get the source meta paths from the template."""
    source_meta_paths = {}

    for name, obj in template.items():
        if name == dataset.__class__.__name__:
            name = ""

        for attr, target in obj.items():
            source_path = "/".join([name, attr])

            if not target.startswith(target_class.__name__):
                continue

            if not source_path.startswith("/"):
                source_path = "/" + source_path
            if not target.startswith("/"):
                target = "/" + target

            source_meta_paths[source_path] = target

    return source_meta_paths


def _convert_value_tree_to_dict(target_dataset: Dict) -> Dict:
    """Transforms the given tree to a dictionary and creates lists
    where indicees are given as keys
    """

    mapped = Nob({})

    for node in levelorder_iter(target_dataset):
        if node.is_leaf:
            mapped[node.path_name] = node.value
            continue

        if all([child.name.isdigit() for child in node.children]):
            mapped[node.path_name] = []
        elif node.name.isdigit():
            mapped[node.parent.path_name].val.append({})
        else:
            mapped[node.path_name] = {}

    return mapped.val


def _get_target_meta_path(path: str, target_meta_paths: List[str]):
    """Gets the target meta paths for a given path, these are then adjusted
    to the indexed explicit paths of the source dataset.
    """

    digit_free_paths = [_digit_free_path(path) for path in target_meta_paths]

    if path in digit_free_paths:
        return target_meta_paths[digit_free_paths.index(path)]

    raise ValueError(f"Path {path} not found in {target_meta_paths}")


def _digit_free_path(path: str):
    """Clears all digits from a path"""
    return re.sub(r"\/\d+\/", "/", path)


def _adjust_index(target_path: str, source_path: str, current_paths: List[str]):
    """This function adjusts the indices of the target path to match the source path

    The intend of this method is to preserve the order of the source dataset by
    adjusting the indices of the target dataset. Consider the following example:

    Source dataset:
        attribute/0/attribute2/0/attribute3
        attribute/0/attribute2/1/attribute3
        attribute/1/attribute2/0/attribute3
        attribute/1/attribute2/1/attribute3

    has to be mapped to the following target dataset in case of a nested model:
        attribute/0/attribute2/0/attribute3/0/attribute4
        attribute/0/attribute2/0/attribute3/1/attribute4
        attribute/0/attribute2/1/attribute3/0/attribute4
        attribute/0/attribute2/1/attribute3/1/attribute
    """

    # First, check the current paths for the target path
    similar_paths = [
        path
        for path in current_paths
        if _digit_free_path(target_path) == _digit_free_path(path)
    ]

    # Build a reverse order of indices
    index_order = [int(part) for part in source_path.split("/")[::-1] if part.isdigit()]

    # If there are similar paths, check if the given indices are lower or equal to the
    # ones of the current paths. If so, adjust the indices by adding one
    if similar_paths:
        index_order = _update_index_order(similar_paths, index_order)

    # Re-build the path and include the new index order
    new_path = []

    for part in target_path.split("/")[::-1]:
        if not part.isdigit():
            new_path.append(part)
            continue

        if index_order:
            new_path.append(str(index_order.pop(0)))
        else:
            new_path.append(part)

    return "/".join(new_path[::-1])


def _update_index_order(similar_paths: List[str], index_order: List[int]):
    """Updates the index order to prevent redundant indices.

    Specifically, this function checks if the given index order is lower or equal
    to the maximum index order of the similar paths. If so, the index order is
    increased by one.

    Example:

        Suppose the following paths are given to be mapped to the same target:

        source1_tgt = "path/0/path2/0/path3"
        source2_tgt = "path/0/path2/0/path3"

        Then, to prevent redundant indices, the index order of the second path
        will be increased by one. Resulting in:

        source1_tgt = "path/0/path2/0/path3"
        source2_tgt = "path/0/path2/1/path3"

    Args:
        similar_paths (List[str]): List of similar meta paths
        index_order (List[int]): Index order of the current path

    Returns:
        List[int]: Updated index order
    """

    max_index_order = max(
        [
            [int(part) for part in path.split("/")[::-1] if part.isdigit()]
            for path in similar_paths
        ]
    )

    if max_index_order == index_order:
        return [index + 1 for index in max_index_order]
    elif max_index_order[-1] >= index_order[-1]:
        index_order[-1] = max_index_order[-1] + 1

    return index_order
