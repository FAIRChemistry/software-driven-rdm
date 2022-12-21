from enum import Enum


class DataTypes(Enum):
    """Holds Data Type mappings"""

    string = ("str", None)
    str = ("str", None)
    float = ("float", None)
    int = ("int", None)
    integer = ("int", None)
    bytes = ("bytes", None)
    EmailStr = ("EmailStr", ["from pydantic import EmailStr"])
    Email = ("EmailStr", ["from pydantic import EmailStr"])
    HttpUrl = ("HttpUrl", ["from pydantic import HttpUrl"])
    HttpURL = ("HttpUrl", ["from pydantic import HttpUrl"])
    httpurl = ("HttpUrl", ["from pydantic import HttpUrl"])
    AnyHttpUrl = ("AnyHttpUrl", ["from pydantic import AnyHttpUrl"])
    AnyHttpURL = ("AnyHttpUrl", ["from pydantic import AnyHttpUrl"])
    anyhttpurl = ("AnyHttpUrl", ["from pydantic import AnyHttpUrl"])
    AnyUrl = ("AnyUrl", ["from pydantic import AnyUrl"])
    URL = ("AnyUrl", ["from pydantic import AnyUrl"])
    posfloat = ("PositiveFloat", ["from pydantic.types import PositiveFloat"])
    PositiveFloat = ("PositiveFloat", ["from pydantic.types import PositiveFloat"])
    positivefloat = ("PositiveFloat", ["from pydantic.types import PositiveFloat"])
    date = ("datetime", ["from datetime import datetime"])
    datetime = ("datetime", ["from datetime import datetime"])
    bool = ("bool", None)
    boolean = ("bool", None)
    Decimal = ("Decimal", ["from pydantic.types import Decimal"])
    decimal = ("Decimal", ["from pydantic.types import Decimal"])
    Enum = ("Enum", ["from pydantic.types import Enum"])
    enum = ("Enum", ["from pydantic.types import Enum"])
    Path = ("Path", ["from pydantic.types import Path"])
    path = ("Path", ["from pydantic.types import Path"])
    Any = ("Any", ["from typing import Any"])
    any = ("Any", ["from typing import Any"])
    Callable = ("Callable", ["from pydantic.types import Callable"])
    callable = ("Callable", ["from pydantic.types import Callable"])
    FrozenSet = ("FrozenSet", ["from pydantic.types import FrozenSet"])
    frozenset = ("FrozenSet", ["from pydantic.types import FrozenSet"])
    Optional = ("Optional", ["from pydantic.types import Optional"])
    optional = ("Optional", ["from pydantic.types import Optional"])
    Pattern = ("Pattern", ["from pydantic.types import Pattern"])
    pattern = ("Pattern", ["from pydantic.types import Pattern"])
    UUID = ("UUID", ["from pydantic.types import UUID"])
    uuid = ("UUID", ["from pydantic.types import UUID"])
    NoneStr = ("NoneStr", ["from pydantic.types import NoneStr"])
    nonestr = ("NoneStr", ["from pydantic.types import NoneStr"])
    NoneBytes = ("NoneBytes", ["from pydantic.types import NoneBytes"])
    nonebytes = ("NoneBytes", ["from pydantic.types import NoneBytes"])
    StrBytes = ("StrBytes", ["from pydantic.types import StrBytes"])
    strbytes = ("StrBytes", ["from pydantic.types import StrBytes"])
    NoneStrBytes = ("NoneStrBytes", ["from pydantic.types import NoneStrBytes"])
    nonestrbytes = ("NoneStrBytes", ["from pydantic.types import NoneStrBytes"])
    OptionalInt = ("OptionalInt", ["from pydantic.types import OptionalInt"])
    optionalint = ("OptionalInt", ["from pydantic.types import OptionalInt"])
    OptionalIntFloat = (
        "OptionalIntFloat",
        ["from pydantic.types import OptionalIntFloat"],
    )
    optionalintfloat = (
        "OptionalIntFloat",
        ["from pydantic.types import OptionalIntFloat"],
    )
    OptionalIntFloatDecimal = (
        "OptionalIntFloatDecimal",
        ["from pydantic.types import OptionalIntFloatDecimal"],
    )
    optionalintfloatdecimal = (
        "OptionalIntFloatDecimal",
        [
            "from pydantic.types import OptionalIntFloatDecimal",
        ],
    )
    StrIntFloat = ("StrIntFloat", ["from pydantic.types import StrIntFloat"])
    strintfloat = ("StrIntFloat", ["from pydantic.types import StrIntFloat"])
    StrictBool = ("StrictBool", ["from pydantic.types import StrictBool"])
    strictbool = ("StrictBool", ["from pydantic.types import StrictBool"])
    PositiveInt = ("PositiveInt", ["from pydantic.types import PositiveInt"])
    positiveint = ("PositiveInt", ["from pydantic.types import PositiveInt"])
    NegativeInt = ("NegativeInt", ["from pydantic.types import NegativeInt"])
    negativeint = ("NegativeInt", ["from pydantic.types import NegativeInt"])
    NonPositiveInt = ("NonPositiveInt", ["from pydantic.types import NonPositiveInt"])
    nonpositiveint = ("NonPositiveInt", ["from pydantic.types import NonPositiveInt"])
    NonNegativeInt = ("NonNegativeInt", ["from pydantic.types import NonNegativeInt"])
    nonnegativeint = ("NonNegativeInt", ["from pydantic.types import NonNegativeInt"])
    StrictInt = ("StrictInt", ["from pydantic.types import StrictInt"])
    strictint = ("StrictInt", ["from pydantic.types import StrictInt"])
    ConstrainedFloat = (
        "ConstrainedFloat",
        ["from pydantic.types import ConstrainedFloat"],
    )
    constrainedfloat = (
        "ConstrainedFloat",
        ["from pydantic.types import ConstrainedFloat"],
    )
    NegativeFloat = ("NegativeFloat", ["from pydantic.types import NegativeFloat"])
    negativefloat = ("NegativeFloat", ["from pydantic.types import NegativeFloat"])
    NonPositiveFloat = (
        "NonPositiveFloat",
        ["from pydantic.types import NonPositiveFloat"],
    )
    nonpositivefloat = (
        "NonPositiveFloat",
        ["from pydantic.types import NonPositiveFloat"],
    )
    NonNegativeFloat = (
        "NonNegativeFloat",
        ["from pydantic.types import NonNegativeFloat"],
    )
    nonnegativefloat = (
        "NonNegativeFloat",
        ["from pydantic.types import NonNegativeFloat"],
    )
    StrictFloat = ("StrictFloat", ["from pydantic.types import StrictFloat"])
    strictfloat = ("StrictFloat", ["from pydantic.types import StrictFloat"])
    StrictBytes = ("StrictBytes", ["from pydantic.types import StrictBytes"])
    strictbytes = ("StrictBytes", ["from pydantic.types import StrictBytes"])
    StrictStr = ("StrictStr", ["from pydantic.types import StrictStr"])
    strictstr = ("StrictStr", ["from pydantic.types import StrictStr"])
    UUID1 = ("UUID1", ["from pydantic.types import UUID1"])
    uuid1 = ("UUID1", ["from pydantic.types import UUID1"])
    UUID3 = ("UUID3", ["from pydantic.types import UUID3"])
    uuid3 = ("UUID3", ["from pydantic.types import UUID3"])
    UUID4 = ("UUID4", ["from pydantic.types import UUID4"])
    uuid4 = ("UUID4", ["from pydantic.types import UUID4"])
    UUID5 = ("UUID5", ["from pydantic.types import UUID5"])
    uuid5 = ("UUID5", ["from pydantic.types import UUID5"])
    FilePath = ("FilePath", ["from pydantic.types import FilePath"])
    filepath = ("FilePath", ["from pydantic.types import FilePath"])
    DirectoryPath = ("DirectoryPath", ["from pydantic.types import DirectoryPath"])
    directorypath = ("DirectoryPath", ["from pydantic.types import DirectoryPath"])
    Json = ("Json", ["from pydantic.types import Json"])
    json = ("Json", ["from pydantic.types import Json"])
    PastDate = ("PastDate", ["from pydantic.types import PastDate"])
    pastdate = ("PastDate", ["from pydantic.types import PastDate"])
    FutureDate = ("FutureDate", ["from pydantic.types import FutureDate"])
    futuredate = ("FutureDate", ["from pydantic.types import FutureDate"])
    NDArray = (
        "Union[NDArray, H5Dataset]",
        [
            "from numpy.typing import NDArray",
            "from h5py._hl.dataset import Dataset as H5Dataset",
            "from typing import Union",
        ],
    )
    ndarray = (
        "Union[NDArray, H5Dataset]",
        [
            "from numpy.typing import NDArray",
            "from h5py._hl.dataset import Dataset as H5Dataset",
            "from typing import Union",
        ],
    )
    ndArray = (
        "Union[NDArray, H5Dataset]",
        [
            "from numpy.typing import NDArray",
            "from h5py._hl.dataset import Dataset as H5Dataset",
            "from typing import Union",
        ],
    )
    H5Dataset = ("H5Dataset", ["from h5py._hl.dataset import Dataset as H5Dataset"])
    h5dataset = ("H5Dataset", ["from h5py._hl.dataset import Dataset as H5Dataset"])

    @classmethod
    def get_value_list(cls):
        return [member.value[0] for member in cls.__members__.values()]
