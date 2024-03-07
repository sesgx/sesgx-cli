from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import tomli
import tomli_w
from dacite import from_dict


@dataclass(frozen=True)
class LDAParams:
    min_document_frequency: List[float]
    n_topics: List[int]


@dataclass(frozen=True)
class BERTopicParams:
    umap_n_neighbors: List[int]
    kmeans_n_clusters: List[int]


@dataclass(frozen=True)
class FormulationParams:
    n_words_per_topic: List[int]
    n_enrichments_per_word: List[int]


@dataclass(frozen=True)
class ExperimentConfig:
    scopus_api_keys: List[str]
    formulation_params: FormulationParams
    lda_params: LDAParams
    bertopic_params: BERTopicParams

    @classmethod
    def from_toml(
        cls,
        path: Path,
    ) -> "ExperimentConfig":
        with open(path, "rb") as f:
            settings_dict = tomli.load(f)

        return from_dict(ExperimentConfig, settings_dict)

    def to_toml(
        self,
        path: Path,
    ) -> None:
        base_config = asdict(self)

        with open(path, "wb") as f:
            tomli_w.dump(base_config, f)

    @classmethod
    def create_default(cls):
        lda_params = LDAParams(
            min_document_frequency=[0.1, 0.2, 0.3, 0.4],
            n_topics=[1, 2, 3, 4, 5],
        )

        bertopic_params = BERTopicParams(
            umap_n_neighbors=[3, 5, 7],
            kmeans_n_clusters=[1, 2, 3, 4, 5],
        )

        string_formulation_params = FormulationParams(
            n_words_per_topic=[5, 6, 7, 8, 9, 10],
            n_enrichments_per_word=[0, 1, 2, 3],
        )

        return ExperimentConfig(
            scopus_api_keys=["key1", "key2", "key3"],
            formulation_params=string_formulation_params,
            lda_params=lda_params,
            bertopic_params=bertopic_params,
        )
