import sdRDM

from pydantic import Field
from typing import Optional


class BiocatalystBase(sdRDM.DataModel):

    """Do fugiat mollit sit duis deserunt dolor ex. Quis do occaecat dolor consectetur nostrud occaecat eu sint aute. Laboris commodo laborum proident id laboris cupidatat amet commodo tempor laborum sint occaecat mollit velit."""

    name: str = Field(
        ...,
        description="Name of the biocatalyst",
    )

    reaction: str = Field(
        ...,
        description="Reaction in which the biocatalyst is activ.",
    )

    sequence: str = Field(
        ...,
        description="Amino acid sequence of the biocatalyst.",
    )

    host_organism: str = Field(
        ...,
        description="Organism used for expression.",
    )

    source_organism: str = Field(
        ...,
        description="Organism the biocatalyst originates from.",
    )

    production_procedure: str = Field(
        ...,
        description="Procedure on how the biocatalyst was synthesized/expressed.",
    )

    isoenzyme: str = Field(
        ...,
        description="Isoenzyme of the biocatalyst.",
    )

    ecnumber: Optional[str] = Field(
        description="Code used to determine the family of a protein.",
        default=None,
    )

    post_translational_mods: Optional[str] = Field(
        description="Post-translational modifications that were made.",
        default=None,
    )

    tissue: Optional[str] = Field(
        description="Tissue in which the reaction is happening.",
        default=None,
    )

    localisation: Optional[str] = Field(
        description="Localisation of the biocatalyst.",
        default=None,
    )
