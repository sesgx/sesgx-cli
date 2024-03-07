from itertools import product
from typing import TYPE_CHECKING

from sqlalchemy import (
    Float,
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


class LDAParams(Base):
    __tablename__ = "lda_params"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    min_document_frequency: Mapped[float] = mapped_column(Float())
    n_topics: Mapped[int] = mapped_column(Integer())

    params: Mapped[list["Params"]] = relationship(
        back_populates="lda_params",
        default_factory=list,
    )

    __table_args__ = (UniqueConstraint("min_document_frequency", "n_topics"),)

    @classmethod
    def get_or_save(
        cls,
        n_topics: int,
        min_document_frequency: float,
        session: Session,
    ):
        stmt = (
            select(LDAParams)
            .where(LDAParams.n_topics == n_topics)
            .where(LDAParams.min_document_frequency == min_document_frequency)
        )

        params = session.execute(stmt).scalar_one_or_none()

        if params is None:
            params = LDAParams(
                min_document_frequency=min_document_frequency,
                n_topics=n_topics,
            )

            session.add(params)
            session.commit()
            session.refresh(params)

        return params

    @classmethod
    def get_or_save_from_params_product(
        cls,
        n_topics_list: list[int],
        min_document_frequency_list: list[float],
        session: Session,
    ) -> list["LDAParams"]:
        return [
            LDAParams.get_or_save(
                n_topics=n_topics,
                min_document_frequency=min_doc_freq,
                session=session,
            )
            for n_topics, min_doc_freq in product(
                n_topics_list,
                min_document_frequency_list,
            )
        ]
