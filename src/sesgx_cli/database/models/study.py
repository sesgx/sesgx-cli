from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .association_tables import experiment_qgs, studies_citations
from .base import Base

if TYPE_CHECKING:
    from .experiment import Experiment
    from .slr import SLR


class Study(Base):
    __tablename__ = "study"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    node_id: Mapped[int] = mapped_column(Integer())
    title: Mapped[str] = mapped_column(Text())
    abstract: Mapped[str] = mapped_column(Text())
    keywords: Mapped[str] = mapped_column(Text())

    references: Mapped[list["Study"]] = relationship(
        secondary=studies_citations,
        primaryjoin=id == studies_citations.c.study_id,
        secondaryjoin=id == studies_citations.c.reference_id,
        backref="cited_by",
        default_factory=list,
        order_by="asc(studies_citations.c.reference_id)",
    )

    slr_id: Mapped[int] = mapped_column(
        ForeignKey("slr.id"),
        init=False,
    )
    slr: Mapped["SLR"] = relationship(
        back_populates="gs",
        init=False,
    )

    experiments: Mapped[list["Experiment"]] = relationship(
        secondary=experiment_qgs,
        back_populates="qgs",
        init=False,
    )
