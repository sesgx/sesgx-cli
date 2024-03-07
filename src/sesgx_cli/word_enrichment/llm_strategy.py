"""Perform word enrichment using BERT."""

from dataclasses import dataclass
from typing import List

from sesgx import WordEnrichmentModel


@dataclass
class LLMWordEnrichmentStrategy(WordEnrichmentModel):
    enrichment_text: str
    model: str

    def enrich(self, word: str) -> List[str]:
        raise NotImplementedError()
