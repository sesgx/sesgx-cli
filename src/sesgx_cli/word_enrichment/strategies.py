from enum import Enum


class WordEnrichmentStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    bert = "bert"
    mistral = "mistral"
    gpt = "gpt-3.5-turbo"
    llama = "llama3"
