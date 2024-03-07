"""Filter out enriched words that are too similar character-wise based on stemming.

Attributes:
    PUNCTUATION (set[str]): Set of punctuation characters. Defaults to `#!python set(string.punctuation)`.
"""  # noqa: E501

from string import punctuation

from nltk.stem import LancasterStemmer  # type: ignore
from rapidfuzz.distance import Levenshtein

PUNCTUATION: set[str] = set(punctuation)


lancaster = LancasterStemmer()


def check_strings_are_distant(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at least 5 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at least 4 units of levenshtein distance, False otherwise.

    Examples:
        >>> check_strings_are_distant("string", "string12345")
        True
        >>> check_strings_are_distant("string", "strng")
        False
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) > levenshtein_distance


def check_strings_are_close(
    s1: str,
    s2: str,
) -> bool:
    """Checks if the given strings have at most 3 units of levenshtein distance.

    Args:
        s1 (str): First string.
        s2 (str): Second string.

    Returns:
        True if the strings have at most 3 units of levenshtein distance, False otherwise.

    Examples:
        >>> check_strings_are_close("string", "big string")
        False
        >>> check_strings_are_close("string", "strng")
        True
    """  # noqa: E501
    levenshtein_distance = 4
    return Levenshtein.distance(str(s1), str(s2)) < levenshtein_distance


def check_stemmed_enriched_word_is_valid(
    stemmed_enriched_word: str,
    *,
    stemmed_word: str,
) -> bool:
    """Checks if the stemmed enriched word is valid.

    A stemmed enriched word is considered valid if it complies the following criteria:

    - It is not equal to the stemmed word
    - It is distant from the stemmed word (see [check_strings_are_distant][sesg.enriched_words.stemming_filter.check_strings_are_distant]).

    Args:
        stemmed_enriched_word (str): The stemmed enriched word.
        stemmed_word (str): The word itself.

    Returns:
        True if the strings are not equal and distant, False otherwise.

    Examples:
        >>> check_stemmed_enriched_word_is_valid(
        ...     "string",
        ...     stemmed_word="string"
        ... )
        False
        >>> check_stemmed_enriched_word_is_valid(
        ...     "string",
        ...     stemmed_word="stringified"
        ... )
        True
    """  # noqa: E501
    not_equal = stemmed_word != stemmed_enriched_word
    distant = check_strings_are_distant(stemmed_enriched_word, stemmed_word)

    return not_equal and distant


def check_stemmed_enriched_word_is_duplicate(
    stemmed_enriched_word: str,
    *,
    stemmed_enriched_words_list: list[str],
) -> bool:
    """Checks if the stemmed enriched word is a duplicate.

    A stemmed enriched word is considered duplicate if it is close to one of the stemmed enriched word in the list.

    Args:
        stemmed_enriched_word (str): The stemmed enriched word.
        stemmed_enriched_words_list (list[str]): List of stemmed words to check against.

    Returns:
        True if the stemmed enriched word is a duplicate, False otherwise.

    Examples:
        >>> check_stemmed_enriched_word_is_duplicate(
        ...     "string",
        ...     stemmed_enriched_words_list=["other", "somewhat"],
        ... )
        False
        >>> check_stemmed_enriched_word_is_duplicate(
        ...     "string",
        ...     stemmed_enriched_words_list=["strng", "something"],
        ... )
        True
    """  # noqa: E501
    for word in stemmed_enriched_words_list:
        is_close = check_strings_are_close(word, stemmed_enriched_word)
        if is_close:
            return True

    return False


def check_word_is_punctuation(
    word: str,
) -> bool:
    """Checks if the given word is not punctuation.

    This function uses `#!python string.punctuation` to get punctuation characters.

    Args:
        word (str): Word to check.

    Returns:
        True if the word is punctuation, False otherwise.

    Examples:
        >>> check_word_is_punctuation("a")
        False
        >>> check_word_is_punctuation(">")
        True
    """
    return word in PUNCTUATION


def check_enriched_word_is_relevant(
    enriched_word: str,
    *,
    stemmed_word: str,
    stemmed_enriched_word: str,
    stemmed_relevant_enriched_words: list[str],
) -> bool:
    """Checks if the given enriched word is relevant.

    A enriched word is considered relevant if it complies the following criteria, in order:

    - It is not a punctuation character (see [check_word_is_punctuation][sesg.enriched_words.stemming_filter.check_word_is_punctuation]).
    - It's stemmed form is valid (see [check_stemmed_enriched_word_is_valid][sesg.enriched_words.stemming_filter.check_stemmed_enriched_word_is_valid]).
    - It's stemmed form is not a duplicate (see [check_stemmed_enriched_word_is_duplicate][sesg.enriched_words.stemming_filter.check_stemmed_enriched_word_is_duplicate]).

    Args:
        enriched_word (str): enriched word to check if is relevant.
        stemmed_word (str): Stemmed form of the original word.
        stemmed_enriched_word (str): Stemmed form of the enriched word.
        stemmed_relevant_enriched_words (list[str]): List of stemmed relevant enriched words to check for duplicates.

    Returns:
        True if the enriched word is relevant, False otherwise.
    """  # noqa: E501
    is_punctuation = check_word_is_punctuation(enriched_word)
    if is_punctuation:
        return False

    is_valid = check_stemmed_enriched_word_is_valid(
        stemmed_enriched_word,
        stemmed_word=stemmed_word,
    )
    if not is_valid:
        return False

    is_duplicate = check_stemmed_enriched_word_is_duplicate(
        stemmed_enriched_word,
        stemmed_enriched_words_list=stemmed_relevant_enriched_words,
    )
    if is_duplicate:
        return False

    return True


def filter_with_stemming(
    word: str,
    *,
    enriched_words_list: list[str],
) -> list[str]:
    """Filters out enriched words that are not relevant.

    A enriched word is kept on the list if it complies the following criteria:

    - It is not a punctuation character (see [check_word_is_punctuation][sesg.enriched_words.stemming_filter.check_word_is_punctuation]).
    - It's stemmed form is valid (see [check_stemmed_enriched_word_is_valid][sesg.enriched_words.stemming_filter.check_stemmed_enriched_word_is_valid]).
    - It's stemmed form is not a duplicate (see [check_stemmed_enriched_word_is_duplicate][sesg.enriched_words.stemming_filter.check_stemmed_enriched_word_is_duplicate]).

    Args:
        word (str): Word that was used as source for the enrichment ones.
        enriched_words_list (list[str]): List with the enriched words.

    Returns:
        List of filtered enriched words.
    """  # noqa: E501
    stemmed_word: str = lancaster.stem(word)

    # list with the filtered enriched words
    relevant_enriched_words: list[str] = []

    # list with the filtered enriched words, but stemmed
    stemmed_relevant_enriched_words: list[str] = []

    for enriched_word in enriched_words_list:
        stemmed_enriched_word = lancaster.stem(enriched_word)

        enriched_word_is_relevant = check_enriched_word_is_relevant(
            enriched_word,
            stemmed_word=stemmed_word,
            stemmed_enriched_word=stemmed_enriched_word,
            stemmed_relevant_enriched_words=stemmed_relevant_enriched_words,
        )

        if not enriched_word_is_relevant:
            continue

        relevant_enriched_words.append(enriched_word)
        stemmed_relevant_enriched_words.append(stemmed_enriched_word)

    return relevant_enriched_words
