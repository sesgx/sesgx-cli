from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    mapped_column,
    relationship,
)

from sesgx_cli.topic_extraction.strategies import TopicExtractionStrategy
from sesgx_cli.word_enrichment.strategies import WordEnrichmentStrategy

from .base import Base
from .bertopic_params import BERTopicParams
from .formulation_params import FormulationParams
from .lda_params import LDAParams
from .llm_params import LLMParams

if TYPE_CHECKING:
    from .experiment import Experiment
    from .search_string import SearchString


class Params(Base):
    __tablename__ = "params"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    word_enrichment_strategy: Mapped[str] = mapped_column(String(25))

    topic_extraction_strategy: Mapped[str] = mapped_column(String(25))

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.id"),
        nullable=False,
    )
    experiment: Mapped["Experiment"] = relationship(
        back_populates="params_list",
    )

    formulation_params_id: Mapped[int] = mapped_column(
        ForeignKey("formulation_params.id"),
        nullable=False,
    )
    formulation_params: Mapped["FormulationParams"] = relationship(
        back_populates="params",
    )

    search_string_id: Mapped[int] = mapped_column(
        ForeignKey("search_string.id"),
        nullable=False,
    )
    search_string: Mapped["SearchString"] = relationship(
        back_populates="params_list",
    )

    lda_params_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lda_params.id"),
        nullable=True,
        default=None,
    )
    lda_params: Mapped[Optional["LDAParams"]] = relationship(
        back_populates="params",
        default=None,
    )

    bertopic_params_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bertopic_params.id"),
        nullable=True,
        default=None,
    )
    bertopic_params: Mapped[Optional["BERTopicParams"]] = relationship(
        back_populates="params",
        default=None,
    )

    llm_params_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("llm_params.id"),
        nullable=True,
        default=None,
    )
    llm_params: Mapped[Optional["LLMParams"]] = relationship(
        back_populates="params",
        default=None,
    )

    __table_args__ = (
        CheckConstraint(
            "lda_params_id is not null or bertopic_params_id is not null or llm_params_id is not null"
        ),
        UniqueConstraint(
            "experiment_id",
            "formulation_params_id",
            "lda_params_id",
            "word_enrichment_strategy",
        ),
        UniqueConstraint(
            "experiment_id",
            "formulation_params_id",
            "bertopic_params_id",
            "word_enrichment_strategy",
        ),
        UniqueConstraint(
            "experiment_id",
            "formulation_params_id",
            "llm_params_id",
            "word_enrichment_strategy",
        ),
    )

    @classmethod
    def get_one_or_none(
        cls,
        experiment_id: int,
        formulation_params_id: int,
        word_enrichment_strategy: WordEnrichmentStrategy,
        topic_extraction_strategy: TopicExtractionStrategy,
        session: Session,
        bertopic_params_id: int | None = None,
        lda_params_id: int | None = None,
        llm_params_id: int | None = None,
    ):
        stmt = select(Params).where(
            Params.experiment_id == experiment_id,
            Params.formulation_params_id == formulation_params_id,
            Params.word_enrichment_strategy == word_enrichment_strategy.value,
        )

        if (
            topic_extraction_strategy.value == TopicExtractionStrategy.bertopic
            and bertopic_params_id is not None
        ):
            stmt = stmt.where(Params.bertopic_params_id == bertopic_params_id)

        if (
            topic_extraction_strategy.value == TopicExtractionStrategy.lda
            and lda_params_id is not None
        ):
            stmt = stmt.where(Params.lda_params_id == lda_params_id)

        if (
            topic_extraction_strategy.value == TopicExtractionStrategy.mistral
            or topic_extraction_strategy.value == TopicExtractionStrategy.gpt
            or topic_extraction_strategy.value == TopicExtractionStrategy.llama
            and llm_params_id is not None
        ):
            stmt = stmt.where(Params.llm_params_id == llm_params_id)

        return session.execute(stmt).scalar_one_or_none()

    # @classmethod
    # def create_with_lda_params(
    #     cls,
    #     formulation_params_list: list[FormulationParams],
    #     lda_params_list: list[LDAParams],
    #     experiment_id: int,
    #     word_enrichment_strategy: str,
    # ):
    #     return [
    #         Params(
    #             experiment_id=experiment_id,
    #             lda_params=lda_params,
    #             lda_params_id=lda_params.id,
    #             formulation_params=formulation_params,
    #             formulation_params_id=formulation_params.id,
    #             word_enrichment_strategy=word_enrichment_strategy,
    #         )
    #         for lda_params, formulation_params in product(
    #             lda_params_list,
    #             formulation_params_list,
    #         )
    #     ]

    # @classmethod
    # def create_with_bertopic_params(
    #     cls,
    #     formulation_params_list: list[FormulationParams],
    #     bertopic_params_list: list[BERTopicParams],
    #     experiment_id: int,
    #     word_enrichment_strategy: str,
    # ):
    #     return [
    #         Params(
    #             experiment_id=experiment_id,
    #             bertopic_params=bertopic_params,
    #             bertopic_params_id=bertopic_params.id,
    #             formulation_params=formulation_params,
    #             formulation_params_id=formulation_params.id,
    #             word_enrichment_strategy=word_enrichment_strategy,
    #         )
    #         for bertopic_params, formulation_params in product(
    #             bertopic_params_list,
    #             formulation_params_list,
    #         )
    #     ]

    # @classmethod
    # def create_with_strategy(
    #     cls,
    #     topic_extraction_strategy: "TopicExtractionStrategy",
    #     word_enrichment_strategy: "WordEnrichmentStrategy",
    #     config: ExperimentConfig,
    #     experiment_id: int,
    #     session: Session,
    # ):
    #     formulation_params_list = FormulationParams.get_or_save_from_params_product(
    #         n_enrichments_per_word_list=config.formulation_params.n_enrichments_per_word,
    #         n_words_per_topic_list=config.formulation_params.n_words_per_topic,
    #         session=session,
    #     )

    #     if topic_extraction_strategy == TopicExtractionStrategy.bertopic:
    #         model_params_list = BERTopicParams.get_or_save_from_params_product(  # noqa: E501
    #             kmeans_n_clusters_list=config.bertopic_params.kmeans_n_clusters,
    #             umap_n_neighbors_list=config.bertopic_params.umap_n_neighbors,
    #             session=session,
    #         )

    #         return cls.create_with_bertopic_params(
    #             formulation_params_list=formulation_params_list,
    #             bertopic_params_list=model_params_list,
    #             experiment_id=experiment_id,
    #             word_enrichment_strategy=word_enrichment_strategy.value,
    #         )

    #     elif topic_extraction_strategy == TopicExtractionStrategy.lda:
    #         model_params_list = LDAParams.get_or_save_from_params_product(
    #             n_topics_list=config.lda_params.n_topics,
    #             min_document_frequency_list=config.lda_params.min_document_frequency,
    #             session=session,
    #         )

    #         return cls.create_with_lda_params(
    #             formulation_params_list=formulation_params_list,
    #             lda_params_list=model_params_list,
    #             experiment_id=experiment_id,
    #             word_enrichment_strategy=word_enrichment_strategy.value,
    #         )
