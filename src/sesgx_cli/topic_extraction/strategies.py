from enum import Enum


class TopicExtractionStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    lda = "lda"
    bertopic = "bertopic"
    mistral = "mistral"
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4o-mini"
    llama = "llama3"
