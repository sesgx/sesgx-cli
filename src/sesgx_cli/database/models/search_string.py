from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Text,
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
    from .search_string_performance import SearchStringPerformance


class SearchString(Base):
    __tablename__ = "search_string"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    string: Mapped[str] = mapped_column(Text(), unique=True)
    params_list: Mapped[list["Params"]] = relationship(
        back_populates="search_string",
        default_factory=list,
    )

    performance: Mapped[Optional["SearchStringPerformance"]] = relationship(
        back_populates="search_string",
        default=None,
    )

    @classmethod
    def get_or_create_by_string(
        cls,
        string: str,
        session: Session,
    ):
        stmt = select(SearchString).where(SearchString.string == string)

        search_string = session.execute(stmt).scalar_one_or_none()

        if search_string is None:
            search_string = SearchString(
                string=string,
            )

        return search_string

    @classmethod
    def get_by_id(cls, id: int, session: Session):
        stmt = select(SearchString).where(SearchString.id == id)

        return session.execute(stmt).scalar_one()
