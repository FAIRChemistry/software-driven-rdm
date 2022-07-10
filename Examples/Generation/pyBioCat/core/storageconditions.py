import sdRDM

from datetime import date
from pydantic import Field
from typing import Optional


class StorageConditions(sdRDM.DataModel):

    """Ut aute ut Lorem veniam proident. Laborum do nisi ut eiusmod in nostrud proident. Commodo nulla ipsum commodo culpa aliqua dolore. Labore exercitation eiusmod ea do tempor. Eiusmod enim mollit sit enim eiusmod anim excepteur veniam culpa minim dolor. Labore aliquip sint laboris quis mollit nostrud cillum dolore elit sunt pariatur aliquip."""

    temperature: Optional[str] = Field(
        description="Temperature of thet storage",
        default=None,
    )

    storing_start: Optional[date] = Field(
        description="Date when catalyst was put into storage.",
        default=None,
    )

    removing: Optional[date] = Field(
        description="Date when catalyst was removed from storage.",
        default=None,
    )

    rethawing: Optional[date] = Field(
        description="Date when catalyst was rethawed from storage.",
        default=None,
    )

    thawing_process: Optional[date] = Field(
        description="Method of thawing.",
        default=None,
    )
