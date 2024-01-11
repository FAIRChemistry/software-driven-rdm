import sdRDM

from typing import Optional
from uuid import uuid4
from pydantic_xml import attr, element
from sdRDM.base.utils import forge_signature


@forge_signature
class SmallType(sdRDM.DataModel):
    """Small type for attribute 'small_type'"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )
    value: Optional[float] = element(
        default=None, tag="float", json_schema_extra=dict()
    )
    name: Optional[str] = element(default=None, tag="string", json_schema_extra=dict())


@forge_signature
class AnotherObject(sdRDM.DataModel):
    """Since the object `AnotherObject` is used as a type in `MyObject`, it needs to be defined as well. Here we will make use of so called `SmallTypes` which can be used on the fly to create sub-objects. Sometimes you might not want to define trivial objects in a separate block and rather define them on the fly. This is where `SmallTypes` come in handy."""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    small_type: Optional[SmallType] = element(
        description="This is an attribute of type string",
        default_factory=SmallType,
        tag="SmallType",
        json_schema_extra=dict(),
    )
