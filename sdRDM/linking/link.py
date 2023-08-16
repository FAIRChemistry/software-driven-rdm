from copy import deepcopy
import re
import validators
from typing import Any, Dict, List, Tuple

from bigtree import dict_to_tree, levelorder_iter, tree_to_dict
from dotted_dict import DottedDict
from nob import Nob
from pydantic.main import ModelMetaclass


def convert_data_model(
    dataset,
    template: Dict = {},
    print_paths: bool = False,
):
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

    global __print_paths__

    if print_paths:
        __print_paths__ = True
    else:
        __print_paths__ = False

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

    if bool(validators.url(source)):  # type: ignore
        return _get_git_source(source, DataModel)

    return DataModel.from_markdown(source)


def _get_git_source(source: str, data_model: "DataModel") -> "DataModel":
    """Fetches a git source from the given string."""

    if _has_tag_or_commit(source):
        commit = re.split(r"@", source)[1].strip()
        url = re.split(r"@", source)[0].strip()

        return data_model.from_git(url=url, commit=commit)
    else:
        return data_model.from_git(url=source)


def _has_tag_or_commit(source: str) -> bool:
    """Checks whether the given source has a tag."""

    if "@" not in source:
        return False

    return True


def _assemble_dataset(
    dataset: "DataModel",
    template: Dict[str, Dict],
    target_class: ModelMetaclass,
) -> Dict:
    """Creates an explicit mapping from the source to the target dataset and transfers values."""

    template = deepcopy(template)

    target_dataset = {}
    explicit_mapping, constants = _construct_explicit_mapping(
        dataset,
        template,
        target_class,
    )

    # Map from dataset to target
    for source, target in explicit_mapping.items():
        value = dataset.get(source)

        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        context = "/".join(_digit_free_path(source).split("/")[:-1])

        if not context:
            context = "/"

        target_dataset[target] = {
            "value": value,
            "context": context,
        }

    # Map constants
    constants_mapping = {}
    for constant in constants:
        target = constant.pop("target")
        constants_mapping.update(
            _process_constant_target(target_dataset, target, constant)
        )

    # Add them to the target dataset
    target_dataset.update(constants_mapping)

    return _convert_value_tree_to_dict(dict_to_tree(target_dataset))  # type: ignore


def _process_constant_target(
    target_dataset: Dict,
    target: str,
    config: Dict,
) -> Dict:
    target_parent = "/" + "/".join(target.split("/")[:-1])
    constants_mapping = {}

    matching_parent_paths = _find_matching_parent_paths(
        target_dataset,
        target_parent,
        config["context"],
    )

    if len(matching_parent_paths) == 1:
        constants_mapping[target] = {"value": config["value"]}
        return constants_mapping

    for parent_path in matching_parent_paths:
        full_path = "/".join([parent_path, target.split("/")[-1]])
        constants_mapping[full_path] = {"value": config["value"]}

    return constants_mapping


def _find_matching_parent_paths(
    target_dataset: Dict,
    target_parent: str,
    context: str,
):
    matching_parents = []

    for path, config in target_dataset.items():
        meta_parent_path = "/".join(_digit_free_path(path).split("/")[:-1])
        same_context = config["context"] == context

        if meta_parent_path == target_parent and same_context:
            matching_parents.append("/".join(path.split("/")[:-1]))

    return list(set(matching_parents))


def _construct_explicit_mapping(
    dataset: "DataModel",
    template: Dict[str, Dict],
    target_class: ModelMetaclass,
):
    """Creates an explicit mapping between the source and target dataset."""

    dataset_paths, source_meta_paths, target_meta_paths, constants = _gather_paths(
        dataset,
        template,
        target_class,
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

        if target_path in explicit_mapping.values():
            target_path = _process_duplicate_path(
                target_path,
                source_path,
                explicit_mapping,
            )

        explicit_mapping[source_path] = target_path

    if globals()["__print_paths__"]:
        for source, target in explicit_mapping.items():
            print(f"{source} -> {target}")

    return explicit_mapping, constants


def _process_duplicate_path(
    target_path: str,
    source_path: str,
    explicit_mapping: Dict[str, str],
):
    """Processes duplicate paths and increments based on the depth diff of both models"""

    same_paths = _get_similar_paths(
        target_path,
        list(explicit_mapping.values()),
    )

    n_digits_source = len(_get_digit_order(source_path))
    n_digits_target = len(_get_digit_order(target_path))

    # Get the diff and thus the index to increment
    diff = n_digits_source - n_digits_target

    if diff < 0:
        raise NotImplementedError(
            f"Target path {target_path} has more indices than source path {source_path}. This functionality is not yet implemented."
        )

    return _adjust_diff_index(target_path, same_paths, diff)


def _adjust_diff_index(
    target_path: str,
    same_paths: List[str],
    diff: int,
):
    """Increments the first index found in the target path"""

    # Get the maximum first index
    max_first_index = _get_max_diff_index(same_paths, diff)

    # Reconstruct the path with the first index incremented by one
    new_path = []
    digit_index = 0

    for part in target_path.split("/"):
        if part.isdigit() and digit_index == diff:
            new_path.append(str(max_first_index + 1))
            digit_index += 1
            continue
        elif part.isdigit() and digit_index != diff:
            digit_index += 1
        else:
            new_path.append(part)

    return "/".join(new_path)


def _get_max_diff_index(same_paths: List[str], diff: int):
    """Gets the maximum first index from a list of paths"""

    return max(
        [
            [int(part) for part in path.split("/") if part.isdigit()][-diff]
            for path in same_paths
        ]
    )


def _get_similar_paths(path: str, paths: List[str]):
    """Gets all paths that are similar to the given path."""

    return [p for p in paths if _digit_free_path(path) == _digit_free_path(p)]


def _gather_paths(
    dataset: "DataModel",
    template: Dict[str, Dict],
    target_class: ModelMetaclass,
) -> Tuple[List, Dict, List, List]:
    """Gathers all the necessary meta and explicit paths.

    Explicit in the sense of strict list indices within the path
    """

    source_meta_paths, constants = _get_source_meta_paths(
        dataset, template, target_class
    )
    dataset_paths = [
        str(path)
        for path in dataset.paths()
        if re.sub(r"\/\d+\/", "/", str(path)) in source_meta_paths
    ]

    target_meta_paths = list(tree_to_dict(target_class.meta_tree(show=False)).keys())  # type: ignore

    return dataset_paths, source_meta_paths, target_meta_paths, constants


def _get_source_meta_paths(
    dataset: "DataModel",
    template: Dict[str, Dict],
    target_class: ModelMetaclass,
) -> Tuple[Dict[str, str], List[Dict]]:
    """Get the source meta paths from the template."""
    source_meta_paths = {}
    constants = []

    for name, obj in template.items():
        if name == dataset.__class__.__name__:
            name = ""

        for attr, target in obj.items():
            source_path = "/".join([name, attr]).replace(".", "/")
            context = "/" + "/".join(source_path.split("/")[:-1])

            if isinstance(target, dict):
                constants += [
                    {
                        "target": target,
                        "value": constant_value,
                        "context": context,
                    }
                    for constant_value, target in target.items()
                ]
                continue

            if not target.startswith(target_class.__name__):
                continue

            if not source_path.startswith("/"):
                source_path = "/" + source_path
            if not target.startswith("/"):
                target = "/" + target

            source_meta_paths[source_path] = target

    return source_meta_paths, constants


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

    all_paths_string = "\n".join(target_meta_paths)

    raise ValueError(f"Path {path} not found in \n\n {all_paths_string}")


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
    # similar_paths = [
    #     path
    #     for path in current_paths
    #     if _digit_free_path(target_path) == _digit_free_path(path)
    # ]

    # Build a reverse order of indices
    source_order = _get_digit_order(source_path)
    target_order = _get_digit_order(target_path)
    diff = len(source_order) - len(target_order)

    if diff > 0:
        source_order = source_order[:-(diff)]
    elif diff < 0:
        raise NotImplementedError(
            f"Target path {target_path} has more indices than source path {source_path}. This functionality is not yet implemented."
        )

    # Re-build the path and include the new index order
    new_path = []

    # Reverse source order
    source_order = source_order[::-1]

    for part in target_path.split("/")[::-1]:
        if not part.isdigit():
            new_path.append(part)
            continue

        if source_order:
            new_path.append(str(source_order.pop(0)))
        else:
            new_path.append(part)

    return "/".join(new_path[::-1])


def _get_digit_order(path: str):
    """Extract the digits within paths.

    Args:
        path (str): The path to parse
    """

    return [int(part) for part in path.split("/") if part.isdigit()]


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
