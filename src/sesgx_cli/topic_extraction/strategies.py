from enum import Enum


class TopicExtractionStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    lda = "lda"
    bertopic = "bertopic"
    mistral = "mistral"
    gpt = "gpt-3.5-turbo"
    llama = "llama3"
