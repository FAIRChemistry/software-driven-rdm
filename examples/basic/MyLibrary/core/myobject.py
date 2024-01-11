import sdRDM

from typing import List, Optional
from uuid import uuid4
from pydantic_xml import attr, element, wrapped
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature

from sdRDM.base.datatypes import Unit

from .anotherobject import AnotherObject
from .anotherobject import SmallType


@forge_signature
class MyObject(
    sdRDM.DataModel,
):
    """This is a description of the object `MyObject`. It can be used to describe the object in more detail. This object includes primitive, mandatory and array attributes:**Types**
    : The type option is a mandatory option that specifies the type of the attribute. You can find a list of all supported types in `sdRDM/generator/datatypes.py`. In addtion to the primitive types, you can also use other objects as types. These will then help you to build more complex data models.**Options**
    : You can include many more options to shape the output of your data model. One of which is `XML` that allows you to specifiy an alias for the serialisation.Lets define the object `MyObject`:
    """

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    attribute: Optional[str] = element(
        description="This is an attribute of type string",
        default=None,
        tag="attribute",
        json_schema_extra=dict(),
    )

    mandatory_attribute: float = element(
        description="This is a mandatory attribute of type string",
        tag="mandatory_attribute",
        json_schema_extra=dict(),
    )

    array_attribute: List[float] = wrapped(
        "array_attribute",
        element(
            description="This is an array attribute of type float",
            default_factory=ListPlus,
            tag="float",
            json_schema_extra=dict(
                multiple=True,
            ),
        ),
    )

    object_attribute: Optional[AnotherObject] = element(
        description="This is an object attribute of type AnotherObject",
        default_factory=AnotherObject,
        tag="object_attribute",
        json_schema_extra=dict(),
    )

    multiple_object_attribute: List[AnotherObject] = wrapped(
        "multiple_object_attribute",
        element(
            description="This is an object attribute of type AnotherObject",
            default_factory=ListPlus,
            tag="AnotherObject",
            json_schema_extra=dict(
                multiple=True,
            ),
        ),
    )

    some_unit: Optional[Unit] = element(
        description="This is an object attribute of type Unit",
        default=None,
        tag="some_unit",
        json_schema_extra=dict(),
    )

    def add_to_multiple_object_attribute(
        self,
        small_type: Optional[SmallType] = None,
        id: Optional[str] = None,
    ) -> AnotherObject:
        """
        This method adds an object of type 'AnotherObject' to attribute multiple_object_attribute

        Args:
            id (str): Unique identifier of the 'AnotherObject' object. Defaults to 'None'.
            small_type (): This is an attribute of type string. Defaults to None
        """

        params = {
            "small_type": small_type,
        }

        if id is not None:
            params["id"] = id

        self.multiple_object_attribute.append(AnotherObject(**params))

        return self.multiple_object_attribute[-1]
