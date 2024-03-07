from enum import Enum


class WordEnrichmentStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    bert = "bert"
