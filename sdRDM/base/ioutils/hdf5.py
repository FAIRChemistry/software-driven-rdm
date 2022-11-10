import numpy as np

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
            
def _write_source(dataset, file: H5File):
    """Writes source information if given"""
    
    # Create a group to add metadata to
    group = file.create_group(name="__source__")
    
    # Get the model name
    group.attrs["root"] = dataset.__class__.__name__
    
    try:
        # Add Git info if given
        if dataset.__repo__: group.attrs["repo"] = dataset.__repo__,  # type: ignore
        group.attrs["commit"] = dataset.__commit__,  # type: ignore
        group.attrs["url"] = dataset.__repo__.replace(".git", f"/tree/{self.__commit__}"),  # type: ignore
    except AttributeError:
        pass
    
def _write_attr(name, value, h5obj: Union[H5File, H5Group]):
    """Writes an attribute to an HDF5 root or group"""
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
    