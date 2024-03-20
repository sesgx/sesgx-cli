from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

if TYPE_CHECKING:
    from .bertopic_params import BERTopicParams
    from .experiment import Experiment
    from .lda_params import LDAParams


class TopicsExtractedCache(Base):
    __tablename__ = "topics_extracted_cache"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.id"),
        nullable=False,
    )

    experiment: Mapped["Experiment"] = relationship(
        back_populates="topics_extracted_cache",
    )

    lda_params_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lda_params.id"),
        nullable=True,
        default=None,
    )

    lda_params: Mapped[Optional["LDAParams"]] = relationship(
        back_populates="topics_extracted_cache",
        default=None,
    )

    bertopic_params_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bertopic_params.id"),
        nullable=True,
        default=None,
    )

    bertopic_params: Mapped[Optional["BERTopicParams"]] = relationship(
        back_populates="topics_extracted_cache",
        default=None,
    )

    topics: Mapped[str] = mapped_column(JSONB(), nullable=False, default=None)

    __table_args__ = (
        CheckConstraint("lda_params_id is not null or bertopic_params_id is not null"),
        UniqueConstraint(
            "experiment_id",
            "lda_params_id",
        ),
        UniqueConstraint(
            "experiment_id",
            "bertopic_params_id",
        ),
    )
