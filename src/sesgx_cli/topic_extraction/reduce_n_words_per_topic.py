def reduce_n_words_per_topic(
    topics: list[list[str]],
    max_n_words_per_topic: int,
) -> list[list[str]]:
    """Reduces the number of words in each topic.

    Args:
        topics (list[list[str]]): List with the topics.
        max_n_words_per_topic (int): Number of words to keep in each topic.

    Returns:
        List with the reduced topics.

    Examples:
        >>> reduce_number_of_words_per_topic([["machine", "learning"], ["code", "smell"]], 1)
        [['machine'], ['code']]
    """  # noqa: E501
    topics = [topic[:max_n_words_per_topic] for topic in topics]

    return topics