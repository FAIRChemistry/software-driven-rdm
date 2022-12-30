import re

from typing import List, Optional, Dict, Tuple
from sdRDM.generator.datatypes import DataTypes

GITHUB_TYPE_PATTERN = r"(http[s]?://[www.]?github.com/[A-Za-z0-9\/\-\.\_]*[.git]?)"


def process_type(dtype: str) -> Tuple[str, bool, Dict]:
    """High-level function that processes given types"""

    # Check for compositions
    is_composite = get_compositions(dtype)

    # Check for external types
    _, externals = check_and_process_github_type(dtype)

    return dtype, is_composite, externals


def get_compositions(dtype: str) -> bool:
    """Checks whether the given type is supported or another class"""

    # Check for GitHub Types -> Should be included in compositions
    cls, _ = process_github_type(dtype)

    return cls not in DataTypes.__members__


def check_and_process_github_type(dtype: str) -> Tuple[str, Dict[str, str]]:
    """Checks and processes external resources from another model"""

    cls, address = process_github_type(dtype)

    if cls is None and address is None:
        return dtype, {}

    assert cls, "External class is not existant"
    assert address, "External address is not existant"

    return cls, {cls: address}


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
