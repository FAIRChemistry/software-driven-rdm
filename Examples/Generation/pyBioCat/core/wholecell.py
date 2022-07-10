from pydantic import Field
from .biocatalystbase import BiocatalystBase


class WholeCell(BiocatalystBase):

    """Fugiat dolor enim aute dolore tempor consectetur commodo commodo occaecat pariatur aute. Incididunt aliqua do ipsum proident do aute cupidatat tempor voluptate mollit eiusmod sunt. Quis duis mollit anim ex nulla enim minim. Incididunt qui commodo cupidatat occaecat dolor ipsum excepteur sint fugiat minim. Enim ipsum adipisicing ut proident enim sunt non."""

    harvesting_method: str = Field(
        ...,
        description="How the cells were harvested.",
    )
