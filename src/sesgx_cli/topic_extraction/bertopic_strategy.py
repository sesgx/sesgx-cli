"""Topic extraction with [BERTopic](https://arxiv.org/abs/2203.05794)."""

from dataclasses import dataclass
from typing import List

from bertopic import BERTopic  # type: ignore
from sesgx import TopicExtractionModel
from sklearn.cluster import KMeans  # type: ignore
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from umap import UMAP  # type: ignore


@dataclass
class BERTopicTopicExtractionStrategy(TopicExtractionModel):
    kmeans_n_clusters: int
    umap_n_neighbors: int

    def extract(self, docs: List[str]) -> List[List[str]]:
        vectorizer_model = CountVectorizer(
            stop_words="english",
            ngram_range=(1, 3),
        )

        umap_model = UMAP(
            n_neighbors=self.umap_n_neighbors,
            # default values used in BERTopic initialization.
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            low_memory=False,
        )

        cluster_model = KMeans(
            n_clusters=self.kmeans_n_clusters,
        )

        topic_model = BERTopic(
            language="english",
            verbose=False,
            hdbscan_model=cluster_model,  # type: ignore
            vectorizer_model=vectorizer_model,
            umap_model=umap_model,
        )

        topic_model.fit_transform(docs)

        # topic_model.get_topics() will return a Mapping where
        # the key is the index of the topic,
        # and the value is a list of tuples
        # the tuple is composed of a word (or token), and its score

        topics: list[list[str]] = [
            [word for word, _ in topic_group]  # type: ignore
            for topic_group in topic_model.get_topics().values()
        ]

        return topics
