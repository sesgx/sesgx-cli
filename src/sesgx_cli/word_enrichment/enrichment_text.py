from typing import TypedDict


class EnrichmentStudy(TypedDict):
    """Data container for a study that will be used to generate an enrichment text.

    Attributes:
        title (str): Title of the study.
        abstract (str): Abstract of the study.

    Examples:
        >>> study: EnrichmentStudy = {
        ...     "title": "machine learning",
        ...     "abstract": "machine learning is often used in the industry with the goal of...",
        ... }
        >>> study
        {'title': 'machine learning', 'abstract': 'machine learning is often used in the industry with the goal of...'}
    """  # noqa: E501

    title: str
    abstract: str


def create_enrichment_text(
    studies_list: list[EnrichmentStudy],
) -> str:
    r"""Creates a piece of text that consists of the concatenation of the title and abstract of each study.

    Args:
        studies_list (list[EnrichmentStudy]): List of studies with title and abstract.

    Returns:
        The enrichment text.

    Examples:
        >>> studies = [
        ...     EnrichmentStudy(title="title1", abstract="abstract1"),
        ...     EnrichmentStudy(title="title2", abstract="abstract2 \r\ntext"),
        ...     EnrichmentStudy(title="title3", abstract="abstract3"),
        ... ]
        >>> create_enrichment_text(studies_list=studies)
        'title1 abstract1\ntitle2 abstract2 #.text\ntitle3 abstract3\n'
    """  # noqa: E501
    enrichment_text = ""
    for study in studies_list:
        title = study["title"]
        abstract = study["abstract"]

        line = f"{title} {abstract}".strip().replace("\r\n", "#.") + "\n"
        enrichment_text += line

    return enrichment_text
