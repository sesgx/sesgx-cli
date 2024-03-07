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


class BERTopicParams(Base):
    __tablename__ = "bertopic_params"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    kmeans_n_clusters: Mapped[int] = mapped_column(Integer())
    umap_n_neighbors: Mapped[int] = mapped_column(Integer())

    params: Mapped[list["Params"]] = relationship(
        back_populates="bertopic_params",
        default_factory=list,
    )

    __table_args__ = (UniqueConstraint("kmeans_n_clusters", "umap_n_neighbors"),)

    @classmethod
    def get_or_save(
        cls,
        kmeans_n_clusters: int,
        umap_n_neighbors: int,
        session: Session,
    ):
        stmt = (
            select(BERTopicParams)
            .where(BERTopicParams.kmeans_n_clusters == kmeans_n_clusters)
            .where(BERTopicParams.umap_n_neighbors == umap_n_neighbors)
        )

        params = session.execute(stmt).scalar_one_or_none()

        if params is None:
            params = BERTopicParams(
                umap_n_neighbors=umap_n_neighbors,
                kmeans_n_clusters=kmeans_n_clusters,
            )

            session.add(params)
            session.commit()
            session.refresh(params)

        return params

    @classmethod
    def get_or_save_from_params_product(
        cls,
        kmeans_n_clusters_list: list[int],
        umap_n_neighbors_list: list[int],
        session: Session,
    ) -> list["BERTopicParams"]:
        return [
            BERTopicParams.get_or_save(
                kmeans_n_clusters=kmeans_n_clusters,
                umap_n_neighbors=umap_n_neighbors,
                session=session,
            )
            for kmeans_n_clusters, umap_n_neighbors in product(
                kmeans_n_clusters_list,
                umap_n_neighbors_list,
            )
        ]
