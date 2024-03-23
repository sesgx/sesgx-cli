import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dacite import from_dict
from sqlalchemy import (
    Text,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .experiment import Experiment
    from .study import Study


class SLR(Base):
    __tablename__ = "slr"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    name: Mapped[str] = mapped_column(Text(), unique=True)
    min_publication_year: Mapped[Optional[int]]
    max_publication_year: Mapped[Optional[int]]

    gs: Mapped[list["Study"]] = relationship(
        back_populates="slr",
        order_by="asc(Study.id)",
        default_factory=list,
    )

    experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="slr",
        init=False,
    )

    @classmethod
    def get_by_name(
        cls,
        name: str,
        session: Session,
    ):
        stmt = select(SLR).where(SLR.name == name)

        return session.execute(stmt).scalar_one()

    @cached_property
    def _study_mapping(self) -> dict[int, "Study"]:
        return {s.id: s for s in self.gs}

    def get_study_by_id(self, id: int) -> "Study":
        return self._study_mapping[id]

    def adjacency_list(
        self,
        use_node_id: bool = False,
    ) -> dict[int, list[int]]:
        if use_node_id:
            return {s.node_id: [s.node_id for s in s.references] for s in self.gs}

        return {s.id: [s.id for s in s.references] for s in self.gs}

    @classmethod
    def from_json(cls, path: Path) -> "SLR":
        from .study import Study

        @dataclass
        class SLRJSONData:
            @dataclass
            class SLRJSONStudyData:
                id: int
                title: str
                abstract: str
                keywords: str

            name: str
            gs: list[SLRJSONStudyData]
            min_publication_year: Optional[int]
            max_publication_year: Optional[int]

        with open(
            path,
            "r",
            encoding="utf8",
        ) as f:
            data = json.load(f)

        slr_json = from_dict(SLRJSONData, data)

        slr = SLR(
            name=slr_json.name,
            min_publication_year=slr_json.min_publication_year,
            max_publication_year=slr_json.max_publication_year,
            gs=[
                Study(
                    title=s.title,
                    abstract=s.abstract,
                    keywords=s.keywords,
                    node_id=s.id,
                )
                for s in slr_json.gs
            ],
        )

        return slr

    def get_graph_statistics(self) -> tuple[int, float]:
        """Returns the number of connected components and the mean degree of the graph"""
        adjacency_list = self.adjacency_list()

        from networkx import Graph, number_connected_components

        g = Graph(adjacency_list)
        number_of_components: int = number_connected_components(g)
        degrees = [degree for _, degree in g.degree]  # type: ignore
        mean_degree = sum(degrees) / len(degrees)

        return number_of_components, mean_degree
