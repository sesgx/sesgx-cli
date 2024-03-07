from sqlalchemy import (
    Column,
    ForeignKey,
    Table,
)

from .base import Base

studies_citations = Table(
    "studies_citations",
    Base.metadata,
    Column("study_id", ForeignKey("study.id"), primary_key=True),
    Column("reference_id", ForeignKey("study.id"), primary_key=True),
)

experiment_qgs = Table(
    "experiment_qgs",
    Base.metadata,
    Column("experiment_id", ForeignKey("experiment.id"), primary_key=True),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

qgs_in_scopus = Table(
    "qgs_in_scopus",
    Base.metadata,
    Column(
        "search_string_performance_id",
        ForeignKey("search_string_performance.id"),
        primary_key=True,
    ),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

gs_in_scopus = Table(
    "gs_in_scopus",
    Base.metadata,
    Column(
        "search_string_performance_id",
        ForeignKey("search_string_performance.id"),
        primary_key=True,
    ),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

gs_in_bsb = Table(
    "gs_in_bsb",
    Base.metadata,
    Column(
        "search_string_performance_id",
        ForeignKey("search_string_performance.id"),
        primary_key=True,
    ),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)

gs_in_sb = Table(
    "gs_in_sb",
    Base.metadata,
    Column(
        "search_string_performance_id",
        ForeignKey("search_string_performance.id"),
        primary_key=True,
    ),
    Column("study_id", ForeignKey("study.id"), primary_key=True),
)
