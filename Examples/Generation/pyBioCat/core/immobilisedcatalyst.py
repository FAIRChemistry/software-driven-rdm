from pydantic import Field
from .solublebiocatalyst import SolubleBiocatalyst


class ImmobilisedCatalyst(SolubleBiocatalyst):

    """Laboris aliquip cupidatat id aliqua magna. Minim consectetur enim dolor qui laborum aute nisi. Sit quis aute aliquip labore anim quis consequat consequat anim nulla consequat in Lorem. Fugiat cupidatat nostrud nostrud enim in. Proident in fugiat excepteur elit quis laboris nostrud veniam cillum elit culpa. Excepteur qui irure ipsum eu. Officia exercitation ut dolor anim nulla Lorem ut incididunt amet aute do."""

    purification: str = Field(
        ...,
        description="How the biocatalyst was purified.",
    )

    immobilisation_procedure: str = Field(
        ...,
        description="How the biocatalyst was immobilised",
    )
