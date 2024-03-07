from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

if TYPE_CHECKING:
    from .enriched_words_cache_key import EnrichedWordsCacheKey


class CachedEnrichedWords(Base):
    __tablename__ = "cached_enriched_words"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    word: Mapped[str] = mapped_column(Text())

    enriched_words_cache_key_id: Mapped[int] = mapped_column(
        ForeignKey("enriched_words_cache_keys.id"),
        nullable=False,
        default=None,
    )
    enriched_words_cache_key: Mapped["EnrichedWordsCacheKey"] = relationship(
        back_populates="cached_enriched_words_list",
        default=None,
    )
