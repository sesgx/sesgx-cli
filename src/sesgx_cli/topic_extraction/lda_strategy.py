"""Topic extraction with [LDA (Latent Dirichlet Allocation)](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf?ref=https://githubhelp.com)."""

from dataclasses import dataclass
from typing import List

from sesgx import TopicExtractionModel
from sklearn.decomposition import LatentDirichletAllocation  # type: ignore
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore


def reduce_number_of_words_per_topic(
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


@dataclass
class LDATopicExtractionStrategy(TopicExtractionModel):
    min_document_frequency: float
    n_topics: int
    max_n_words_per_topic: int

    def extract(self, docs: List[str]) -> List[List[str]]:
        vectorizer = CountVectorizer(
            min_df=self.min_document_frequency,
            max_df=1.0,
            ngram_range=(1, 3),
            max_features=None,
            stop_words="english",
        )

        tf = vectorizer.fit_transform(docs)

        # `feature_names` is a list with the vectorized words from the document.
        # meaning `feature_names[i]` is a token in the text.
        feature_names = vectorizer.get_feature_names_out()

        alpha = None
        beta = None
        learning = "batch"  # Batch or Online

        # Run the Latent Dirichlet Allocation (LDA) algorithm and train it.
        lda = LatentDirichletAllocation(
            n_components=self.n_topics,
            doc_topic_prior=alpha,
            topic_word_prior=beta,
            learning_method=learning,
            learning_decay=0.7,
            learning_offset=10.0,
            max_iter=5000,
            batch_size=128,
            evaluate_every=-1,
            total_samples=1000000.0,
            perp_tol=0.1,
            mean_change_tol=0.001,
            max_doc_update_iter=100,
            random_state=0,
        )

        lda.fit(tf)

        # `lda.components_` hold the entire list of topics found by LDA.
        # notice that for `lda.components_`, the topic is a list of indexes
        # where the index will map to a token (~word) in `feature_names`.
        # as an example, the next line gets all tokens of the first topic

        # first_topic = lda.components_[0]
        # topic_words = [feature_names[i] for i in first_topic]

        # `topic.argsort()` will return the indexes that would sort the topics,
        # in ascending order
        # since we want the most latent topics, we reverse the list with `[::-1]`

        topics: list[list[str]] = [
            [feature_names[i] for i in topic.argsort()[::-1]]
            for topic in lda.components_
        ]  # type: ignore

        topics = reduce_number_of_words_per_topic(
            topics, self.max_n_words_per_topic)

        return topics