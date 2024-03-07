from itertools import product
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    mapped_column,
    relationship,
)

from .base import Base

if TYPE_CHECKING:
    from .params import Params


class FormulationParams(Base):
    __tablename__ = "formulation_params"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    n_words_per_topic: Mapped[int] = mapped_column(Integer())
    n_enrichments_per_word: Mapped[int] = mapped_column(Integer())

    params: Mapped[list["Params"]] = relationship(
        back_populates="formulation_params",
        default_factory=list,
    )

    __table_args__ = (UniqueConstraint("n_words_per_topic", "n_enrichments_per_word"),)

    @classmethod
    def get_or_save(
        cls,
        n_words_per_topic: int,
        n_enrichments_per_word: int,
        session: Session,
    ):
        stmt = (
            select(FormulationParams)
            .where(FormulationParams.n_words_per_topic == n_words_per_topic)
            .where(FormulationParams.n_enrichments_per_word == n_enrichments_per_word)
        )

        params = session.execute(stmt).scalar_one_or_none()

        if params is None:
            params = FormulationParams(
                n_enrichments_per_word=n_enrichments_per_word,
                n_words_per_topic=n_words_per_topic,
            )

            session.add(params)
            session.commit()
            session.refresh(params)

        return params

    @classmethod
    def get_or_save_from_params_product(
        cls,
        n_words_per_topic_list: list[int],
        n_enrichments_per_word_list: list[int],
        session: Session,
    ) -> list["FormulationParams"]:
        return [
            FormulationParams.get_or_save(
                n_words_per_topic=n_words_per_topic,
                n_enrichments_per_word=n_enrichments_per_word,
                session=session,
            )
            for n_words_per_topic, n_enrichments_per_word in product(
                n_words_per_topic_list,
                n_enrichments_per_word_list,
            )
        ]
