import os
import numpy as np

from anytree import findall
from datetime import date, datetime
from numpy.typing import NDArray
from typing import Union

from h5py._hl.dataset import Dataset as H5Dataset
from h5py._hl.files import File as H5File
from h5py._hl.group import Group as H5Group

import h5py


def write_hdf5(dataset, file: Union[H5File, str]):
    """Writes a given sdRDM model to HDF5"""

    if isinstance(file, str):
        file = h5py.File(file, "w")

    _write_source(dataset, file)

    for path in dataset.paths(leaves=True):
        if "__source__" in path:
            continue

        # Fetch data and destination
        data = dataset.get(path)
        prefix, attribute = path.split()
        prefix = str(prefix)

        if str(prefix) == "/":
            # Write root attributes directly
            _write_attr(prefix, dataset.get(path), file)

        # Fetch or create a group
        group = _get_group(file, prefix)

        if isinstance(data, (np.ndarray, H5Dataset)):
            _write_array(attribute, data, group)
        else:
            _write_attr(attribute, data, group)  # type: ignore


def read_hdf5(obj, file):

    tree, _ = obj.create_tree()
    meta_paths = obj.meta_paths(leaves=True)

    for path in meta_paths:
        node = _get_tree_node(tree, path)

        if "/" not in path:
            # Add to root node
            _add_data_to_node(file.attrs[path], node)
            continue

        prefix, attribute = os.path.dirname(path), os.path.basename(path)

        try:
            group = file[prefix]
        except KeyError:
            continue

        arguments = {}
        for entry in group.values():
            node = _get_tree_node(tree, path)

            if attribute in entry.attrs:
                _add_data_to_node(entry.attrs[attribute], node)
            elif attribute in entry:
                _add_data_to_node(entry[attribute], node)

    return tree.build()


def _write_source(dataset, file: H5File):
    """Writes source information if given"""

    # Create a group to add metadata to
    group = file.create_group(name="__source__")

    # Get the model name
    group.attrs["root"] = dataset.__class__.__name__

    try:
        # Add Git info if given
        if dataset.__repo__:
            group.attrs["repo"] = (dataset.__repo__,)  # type: ignore
        group.attrs["commit"] = (dataset.__commit__,)  # type: ignore
        group.attrs["url"] = (dataset.__repo__.replace(".git", f"/tree/{dataset.__commit__}"),)  # type: ignore
    except AttributeError:
        pass


def _write_attr(name, value, h5obj: Union[H5File, H5Group]):
    """Writes an attribute to an HDF5 root or group"""

    if isinstance(value, (date, datetime)):
        # HDF5 does not like date types
        value = str(value)

    h5obj.attrs[name] = value


def _write_array(name, data: Union[NDArray, H5Dataset], group):
    """Writes an ndarray to an HDF5 file"""

    dataset = group.create_dataset(name=name, shape=data.shape)
    dataset[:] = data


def _get_group(file: H5File, prefix: str):
    """Fetches or creates an HDF5 group"""
    try:
        # Create a group for the prefix ...
        return file.create_group(prefix)
    except ValueError:
        # ... else just fetch it
        return file[prefix]


def _get_tree_node(tree, path):
    result = findall(
        tree,
        filter_=lambda node: "/".join(
            [n.name for n in node.path if n.name[0].islower()]
        )
        == path,
    )

    if len(result) == 0:
        raise ValueError(f"Cant find corresponding node under path '{path}'")
    elif len(result) > 1:
        raise ValueError(f"Found multiple paths for '{path}', which can not be mapped")

    return result[0]


def _add_data_to_node(value, node):
    """Adds data to a given attribute node"""

    # Get lowest value in of node
    if node.value == {}:
        index = 0
    else:
        index = max(node.value.keys()) + 1

    # Add the data to the node
    node.value[index] = value
