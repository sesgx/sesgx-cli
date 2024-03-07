from enum import Enum


class TopicExtractionStrategy(str, Enum):
    """Enum defining the available topic extraction strategies."""

    lda = "lda"
    bertopic = "bertopic"
