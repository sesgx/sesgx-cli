"""Perform word enrichment using LLM models."""

from string import punctuation
from typing import List

from langchain_community.llms import Ollama
from langchain_core.output_parsers.json import SimpleJsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sesgx import WordEnrichmentModel
from tenacity import retry, stop_after_attempt

from .stemming_filter import filter_with_stemming

_PUNCTUATION: set[str] = set(punctuation) - {"'", "-"}


class Prompts:
    """
    Creates a wrapper for possibles prompts to pass to the llm model.
    In this implementation is possible to define the amount of synonyms
    to be generated. By default, it is 7.
    """

    base_prompt = {
        "system": "You are a helpful synonym generator. Answer with a JSON object and nothing more. Follow this example 'synonyms': ['house', 'home']",
        "human": "Given the following context: {context}. Generate this amount of synonyms: {number_similar_words} for this topic: {word_to_be_enriched}.",
    }

    def __init__(self, prompt_text: dict = base_prompt) -> None:  # noqa: D107
        self.prompt_text: dict = prompt_text
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt_text["system"]),
                ("human", self.prompt_text["human"]),
            ]
        )


class LLMWordEnrichmentStrategy(WordEnrichmentModel):
    def __init__(
        self,  # noqa: D107
        enrichment_text: str,
        model: str = "mistral",
        prompt: ChatPromptTemplate = Prompts().prompt,
    ):
        self.model = model
        self.prompt = prompt

        self.llm: ChatOpenAI | Ollama

        self.enrichment_text: str = enrichment_text
        self.number_similar_words: int = 7
        self.init_model()

    def init_model(self) -> None:
        json_parser = SimpleJsonOutputParser()

        self.llm = (
            ChatOpenAI(model=self.model)
            if "gpt" in self.model
            else Ollama(model=self.model)
        )

        self.chain = self.prompt | self.llm | json_parser

    @staticmethod
    def _get_similar_words(response: dict, word: str) -> list[str]:
        """Get the similar words generate by the model. Response treatments are done here.

        Args:
            response (dict): Response returned by the model.
            word (str): Word to be enriched.
        Raises:
            RuntimeError: If the model does not return a well structured response.
        Returns:
            similar_words (list[str]): List of similar words.
        """
        similar_words = response.get("synonyms", None)

        if similar_words is None:
            similar_words = next(
                (response[i] for i in response if isinstance(response[i], list)), None
            )

        if similar_words is None:
            raise RuntimeError(
                f"No similar words returned or the response is not well structured. Response: {response}"
            )

        if word in similar_words:
            similar_words.remove(word)

        for word_idx, word in enumerate(similar_words):
            for char in word:
                if char in _PUNCTUATION:
                    similar_words[word_idx] = word.replace(char, " ")

        return similar_words

    @retry(stop=stop_after_attempt(3))
    def _invoke_model(self, context: str, word: str) -> list[str]:
        response = self.chain.invoke(
            {
                "context": context,
                "number_similar_words": self.number_similar_words,
                "word_to_be_enriched": word,
            }
        )

        similar_words = self._get_similar_words(response, word)

        return similar_words

    def enrich(self, word: str) -> List[str]:
        """Generates similar words using LLMs.

        Args:
            word (str): The word to be enriched.

        Returns:
            A list of similar words.
        """
        selected_sentences: list[str] = []

        for sentence in self.enrichment_text.split("."):
            if word in sentence or word in sentence.lower():
                selected_sentences.append(sentence + ".")
                break

        context = " ".join(selected_sentences)

        similar_words = self._invoke_model(context, word)

        similar_words_after_stemming = filter_with_stemming(
            word,
            enriched_words_list=similar_words,
        )

        return similar_words_after_stemming
