from enum import Enum


class WordEnrichmentStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    bert = "bert"
    mistral = "mistral"
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4o-mini"
    llama = "llama3"
