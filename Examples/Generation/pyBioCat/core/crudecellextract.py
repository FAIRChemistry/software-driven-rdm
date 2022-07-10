from pydantic import Field
from typing import Optional
from .solublebiocatalyst import SolubleBiocatalyst


class CrudeCellExtract(SolubleBiocatalyst):

    """Fugiat fugiat nulla mollit officia exercitation adipisicing et labore proident nostrud proident fugiat. Voluptate esse mollit nulla tempor proident laborum et voluptate eu sit commodo. Elit consequat consectetur excepteur nulla irure qui. Proident labore esse ipsum Lorem eiusmod labore tempor consequat est esse deserunt. Fugiat aliqua sit tempor incididunt qui."""

    cell_disruption_process: str = Field(
        ...,
        description="Method used to disrupt cells.",
    )

    purity_determination: Optional[str] = Field(
        description="Method that was used to determine the purity of the extract.",
        default=None,
    )
