from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

if TYPE_CHECKING:
    from .cached_enriched_words import CachedEnrichedWords
    from .experiment import Experiment


class EnrichedWordsCacheKey(Base):
    __tablename__ = "enriched_words_cache_keys"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    word_enrichment_strategy: Mapped[str] = mapped_column(String(25))

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.id"),
        nullable=False,
    )
    experiment: Mapped["Experiment"] = relationship(
        back_populates="enriched_words_cache_keys",
    )

    word: Mapped[str] = mapped_column(Text())

    cached_enriched_words_list: Mapped[list["CachedEnrichedWords"]] = relationship(
        back_populates="enriched_words_cache_key",
        default_factory=list,
    )

    __table_args__ = (
        UniqueConstraint("experiment_id", "word", "word_enrichment_strategy"),
    )
