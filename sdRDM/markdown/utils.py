import re

from typing import List, Optional, Dict, Tuple
from sdRDM.generator.datatypes import DataTypes

GITHUB_TYPE_PATTERN = r"(http[s]?://[www.]?github.com/[A-Za-z0-9\/\-\.\_]*[.git]?)"


def process_types(type_string: str):
    """High-level function that processes given types"""

    # Check for multiple types
    dtypes = type_string.split(",")

    # Check for compositions
    compositions = list(map(get_sub_class_type, dtypes))

    # Check for external types
    externals = check_and_process_github_types(dtypes)

    if len(dtypes) > 1:
        # Turn into union for multiple types
        dtype = f"Union[{', '.join(dtypes)}]"
    else:
        dtype = dtypes[0]

    return dtype, compositions, externals


def get_sub_class_type(dtype: str) -> Optional[str]:
    """Checks whether the given type is supported or another class"""

    # Check for GitHub Types
    cls, _ = process_github_type(dtype)

    if cls is not None:
        dtype = cls

    if dtype not in DataTypes.__members__:
        return dtype


def check_and_process_github_types(dtypes: List[str]) -> Dict:
    """Checks and processes external resources from another model"""

    externals = {}

    for i, dtype in enumerate(dtypes):

        cls, address = process_github_type(dtype)

        if cls is None and address is None:
            continue

        externals[cls] = address
        dtypes[i] = cls

    return externals


def process_github_type(dtype: str) -> Tuple[Optional[str], Optional[str]]:
    """Processes a given GitHub link"""

    if not "@" in dtype:
        return None, None

        # Split the given link
    address, cls = dtype.split("@")

    if not bool(re.match(GITHUB_TYPE_PATTERN, address)):
        raise ValueError(
            f"Given external type {address} is not a valid GitHub URL - Please inspect syntax rules."
        )

    return cls, address