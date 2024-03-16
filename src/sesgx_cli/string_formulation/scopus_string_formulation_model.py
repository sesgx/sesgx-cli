from dataclasses import dataclass
from typing import Dict, List

from sesgx import (
    DefaultStringFormulationModel,
    StringFormulationModel,
    StringFormulationModelForEnrichment,
)


class InvalidPubyearBoundariesError(ValueError):
    """The provided pubyear boundaries are invalid."""


def set_pub_year_boundaries(
    string: str,
    *,
    min_year: int | None = None,
    max_year: int | None = None,
) -> str:
    """Given a search string, will append `PUBYEAR >` and `PUBYEAR <` boundaries as needed.

    Args:
        string (str): A search string.
        min_year (int | None, optional): Minimum year of publication. Defaults to None.
        max_year (int | None, optional): Maximum year of publication. Defaults to None.

    Returns:
        A search string with PUBYEAR boundaries.

    Examples:
        >>> set_pub_year_boundaries(string='title("machine" and "learning")', max_year=2018)
        'title("machine" and "learning") AND PUBYEAR < 2018'
    """  # noqa: E501
    if min_year is not None and max_year is not None and min_year >= max_year:
        raise InvalidPubyearBoundariesError(
            "Max year must be greater than min year")

    if min_year is not None:
        string += f" AND PUBYEAR > {min_year}"

    if max_year is not None:
        string += f" AND PUBYEAR < {max_year}"

    return string


@dataclass
class ScopusStringFormulationModel(StringFormulationModel):
    """A model for formulating a search string for Scopus."""

    n_words_per_topic: int
    use_enriched_string_formulation_model: bool = False
    min_year: int | None = None
    max_year: int | None = None

    def formulate(self, data: List[Dict[str, List[str]]]) -> str:

        if self.use_enriched_string_formulation_model:
            s = StringFormulationModelForEnrichment().formulate(data)

        else:
            s = DefaultStringFormulationModel().formulate(data)

        s = f"TITLE-ABS-KEY({s})"

        return set_pub_year_boundaries(
            s,
            min_year=self.min_year,
            max_year=self.max_year,
        )
