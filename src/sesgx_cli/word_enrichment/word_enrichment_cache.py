from dataclasses import dataclass
from typing import List

from sesgx import WordEnrichmentModel
from sesgx_cli.database.models import (
    CachedEnrichedWords,
    EnrichedWordsCacheKey,
    Experiment,
)
from sesgx_cli.word_enrichment.strategies import WordEnrichmentStrategy
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload


@dataclass
class WordEnrichmentCache(WordEnrichmentModel):
    word_enrichment_model: WordEnrichmentModel
    word_enrichment_strategy: WordEnrichmentStrategy
    session: Session
    experiment: Experiment
    n_enrichments: int

    def get_from_cache(self, key: str) -> list[str] | None:
        stmt = (
            select(EnrichedWordsCacheKey)
            .options(joinedload(EnrichedWordsCacheKey.cached_enriched_words_list))
            .where(EnrichedWordsCacheKey.experiment_id == self.experiment.id)
            .where(EnrichedWordsCacheKey.word == key)
            .where(
                EnrichedWordsCacheKey.word_enrichment_strategy
                == self.word_enrichment_strategy.value
            )
        )

        result = self.session.execute(stmt).unique().scalar_one_or_none()

        if result is None:
            return None

        return [cached_word.word for cached_word in result.cached_enriched_words_list]

    def save_on_cache(self, key: str, value: list[str]) -> None:
        s = EnrichedWordsCacheKey(
            experiment_id=self.experiment.id,
            experiment=self.experiment,
            word_enrichment_strategy=self.word_enrichment_strategy.value,
            word=key,
            cached_enriched_words_list=[
                CachedEnrichedWords(
                    word=w,
                )
                for w in value
            ],
        )

        self.session.add(s)
        self.session.commit()

    def enrich(self, word: str) -> List[str]:
        enriched_words = self.get_from_cache(word)
        if enriched_words is None:
            enriched_words = self.word_enrichment_model.enrich(word)
            self.save_on_cache(word, enriched_words)

        enriched_words_reduced = enriched_words[: self.n_enrichments]

        return enriched_words_reduced
