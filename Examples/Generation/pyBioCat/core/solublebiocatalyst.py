from datetime import date
from pydantic import Field
from pydantic.types import PositiveFloat
from typing import List
from typing import Optional
from .biocatalystbase import BiocatalystBase
from .storageconditions import StorageConditions


class SolubleBiocatalyst(BiocatalystBase):

    """Irure dolore dolore non sit adipisicing anim commodo est laborum. Proident do do velit eiusmod. Amet aliquip mollit aliqua voluptate eu. Proident ut id Lorem fugiat fugiat cillum ex. Aliqua excepteur laborum quis qui minim esse. Proident magna nostrud pariatur eiusmod nisi excepteur cillum sunt ad deserunt sint culpa ut proident. Esse ex qui occaecat aliquip ipsum exercitation amet ullamco laborum ea commodo exercitation do."""

    concentration: PositiveFloat = Field(
        ...,
        description="Concentration of the biocatalyst.",
    )

    concentration_det_method: str = Field(
        ...,
        description="Method on how the concentration has been determined.",
    )

    storage: List[StorageConditions] = Field(
        description="How the soluble biocatalyst has been stored.",
        default_factory=list,
    )

    def add_to_storage(
        self,
        temperature: Optional[str] = None,
        storing_start: Optional[date] = None,
        removing: Optional[date] = None,
        rethawing: Optional[date] = None,
        thawing_process: Optional[date] = None,
    ) -> None:
        """
        Adds an instance of 'StorageConditions' to the attribute 'storage'.

        Args:
            temperature (Optional[str]): Temperature of thet storage. Defaults to None
            storing_start (Optional[date]): Date when catalyst was put into storage. Defaults to None
            removing (Optional[date]): Date when catalyst was removed from storage. Defaults to None
            rethawing (Optional[date]): Date when catalyst was rethawed from storage. Defaults to None
            thawing_process (Optional[date]): Method of thawing. Defaults to None
        """

        self.storage.append(
            StorageConditions(
                temperature=temperature,
                storing_start=storing_start,
                removing=removing,
                rethawing=rethawing,
                thawing_process=thawing_process,
            )
        )
