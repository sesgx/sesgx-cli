"""Topic extraction with LLM"""

import warnings
from typing import List

from langchain_community.llms import Ollama
from langchain_core.output_parsers.json import SimpleJsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sesgx import TopicExtractionModel
from sklearn.cluster import KMeans
from tenacity import retry, stop_after_attempt, wait_fixed
from umap import UMAP  # type: ignore

warnings.simplefilter(action="ignore", category=FutureWarning)


class Prompts:
    """
    Creates a wrapper for possibles prompts to pass to the llm model.
    In this implementation is possible to define the amount of synonyms
    to be generated. By default, it is 7.
    """

    base_prompt = {
        "system": """You are a helpful keywords extractor. From now on consider that a keyword is a word that 
                      can describe a document. You have to return only a JSON object and nothing more,
                      follow this example: 'keywords':  [set, of , words].
                      I will provide you with some documents as context so you can extract a set of keywords.""",
        "human": """Given the following documents: {context}. Generate a set of keywords with 15 keywords.
                      Please do not generate any more or any less than I've asked and remember to structure your reponse
                      as a JSON object.""",
    }

    def __init__(self, prompt_text: dict = base_prompt) -> None:  # noqa: D107
        self.prompt_text: dict = prompt_text
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_text["system"]),
                ("human", self.prompt_text["human"]),
            ]
        )


class LLMTopicExtractionStrategy(TopicExtractionModel):
    def __init__(
        self,
        kmeans_n_clusters: int,
        umap_n_neighbors: int,
        max_n_words_per_topic: int,
        model: str = "mistral",
        prompt: ChatPromptTemplate = Prompts().prompt,
        sentence_transformer_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.kmeans_n_clusters = kmeans_n_clusters
        self.umap_n_neighbors = umap_n_neighbors
        self.max_n_words_per_topic = max_n_words_per_topic
        self.sentence_transformer_model = sentence_transformer_model

        self.model = model
        self.prompt = prompt
        self.json_parser = SimpleJsonOutputParser()

        self.llm: ChatOpenAI | Ollama

        self.embedding_model: SentenceTransformer

        self.init_model()

    def init_model(self) -> None:
        self.llm = (
            ChatOpenAI(model=self.model)
            if "gpt" in self.model
            else Ollama(model=self.model)
        )

        self.chain = self.prompt | self.llm

        self.embedding_model = SentenceTransformer(
            self.sentence_transformer_model,
            device="cpu",
        )

    def extract(self, docs: List[str]) -> List[List[str]]:
        cluster_model = KMeans(
            n_clusters=self.kmeans_n_clusters,
        )

        umap_model = UMAP(
            n_neighbors=self.umap_n_neighbors,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            low_memory=False,
        )

        embeddings = self.embedding_model.encode(
            docs,
            show_progress_bar=False,
        )
        reduced_embeddings = umap_model.fit_transform(embeddings)
        clusters = cluster_model.fit(reduced_embeddings)

        docs_clusters = {cluster_id: "" for cluster_id in range(self.kmeans_n_clusters)}
        for idx, value in enumerate(clusters.labels_):
            docs_clusters[value] += f" {docs[idx]}"

        topics = []
        for _, context in docs_clusters.items():
            topics.append(self._invoke_model(context))

        return topics

    @staticmethod
    def _get_topics(response: dict) -> List[str]:
        try:
            topics = response.get("Keywords", None)
        except AttributeError:
            raise RuntimeError(f"RESPONSE: {response}")

        if topics is None:
            raise RuntimeError(
                f"No topics returned or unstructured response. Reponse: {response}"
            )

        return topics

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(30), reraise=True)
    def _invoke_model(
        self,
        context: str,
    ) -> list[str]:
        response = self.chain.invoke(
            {
                "context": context,
            }
        )

        response = self.json_parser.parse(response)

        topics = self._get_topics(dict(response))

        return topics
