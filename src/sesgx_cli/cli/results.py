from itertools import product
from pathlib import Path

import pandas as pd
import typer
from rich.progress import Progress

from sesgx_cli.database import Session
from sesgx_cli.database.models import SLR
from sesgx_cli.database.util.db_query_execution import (
    get_results_from_db,
    get_strategies_used,
)
from sesgx_cli.database.util.results_queries import ResultQuery, SideQueries

_AVAILABLE_METRICS = ["start_set_f1_score", "bsb_recall", "sb_recall"]
_DEFAULT_METRICS = ["start_set_precision", "start_set_recall"]

app = typer.Typer(rich_markup_mode="markdown", help="Get experiments' results.")


class InvalidMetric(Exception):
    """The metric passed as a parameter is not valid"""


def verify_metrics(metrics: list[str] | None) -> None:
    if not set(metrics or []).issubset(set(_AVAILABLE_METRICS)):
        raise InvalidMetric()


def _adjust_max_col_width(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str):
    for column in df:
        max_col_width = max(df[column].astype(str).map(len).max(), len(column))  # type: ignore
        col_idx = df.columns.get_loc(column)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, max_col_width)


def _graph_tab(slr_name: str, excel_writer: pd.ExcelWriter):
    sheet_name = "graph_info"

    with Session() as session:
        slr = SLR.get_by_name(slr_name, session)
        number_of_components, mean_degree = slr.get_graph_statistics()

    data = {
        "number_of_components": number_of_components,
        "mean_degree": round(mean_degree, 3),
    }

    df = pd.DataFrame().from_dict(data, orient="index")

    df.rename(columns={0: "values"}, inplace=True)
    df.to_excel(excel_writer=excel_writer, sheet_name=sheet_name)
    excel_writer.sheets[sheet_name].set_column(0, 1, 25)


def _statistics_tab(
    results: dict[str, dict], excel_writer: pd.ExcelWriter, strategies: list[str]
) -> None:
    root_cols = [
        "start_set_precision",
        "start_set_recall",
        "start_set_f1_score",
        "bsb_recall",
        "sb_recall",
        "n_scopus_results",
    ]
    max_cols_highlight = [
        "mean_start_set_precision",
        "mean_start_set_recall",
        "mean_start_set_f1_score",
        "mean_bsb_recall",
        "mean_sb_recall",
    ]

    idx = []
    for col in root_cols:
        idx.append(f"mean_{col}")
        idx.append(f"stdev_{col}")

    stats_df = pd.DataFrame(columns=strategies, index=idx)

    for key, result in results.items():
        temp_df = pd.DataFrame(data=result["data"], columns=result["columns"])
        temp_df = temp_df.drop(temp_df[temp_df["n_scopus_results"] <= 0].index)

        for col in root_cols:
            stats_df.loc[f"mean_{col}", key] = round(temp_df[col].mean(), 5)
            stats_df.loc[f"stdev_{col}", key] = round(temp_df[col].std(), 5)

    stats_df = stats_df.T

    style_stats = stats_df.style.highlight_max(
        subset=max_cols_highlight, color="#8aeda4"
    ).highlight_min(subset=["mean_n_scopus_results"], color="#8aeda4")

    stats_df = stats_df.reset_index()
    stats_df.rename(columns={"index": "strategies"}, inplace=True)

    style_stats.to_excel(excel_writer=excel_writer, sheet_name="stats")
    _adjust_max_col_width(stats_df, excel_writer, "stats")


def save_xlsx(
    excel_writer: pd.ExcelWriter,
    results: dict[str, dict],
    slr: str,
    strategies: list[str],
):
    with Progress() as progress:
        saving_progress = progress.add_task("[green]Saving...", total=len(results))
        with excel_writer:
            for i, (key, result) in enumerate(results.items()):
                df = pd.DataFrame(data=result["data"], columns=result["columns"])

                if "name" in df.columns:
                    cols = df.columns.tolist()
                    cols.remove("name")
                    cols.insert(0, "name")
                    df = df[cols]

                df.to_excel(excel_writer=excel_writer, sheet_name=key, index=False)
                _adjust_max_col_width(df, excel_writer, key)

                progress.update(
                    saving_progress,
                    description=f"[green]Saving {i + 1} of {len(results)}",
                    advance=1,
                    refresh=True,
                )

            overall_results = {
                key: value for key, value in results.items() if key in strategies
            }
            _statistics_tab(overall_results, excel_writer, strategies)
            _graph_tab(slr, excel_writer)

        progress.remove_task(saving_progress)


def get_results(slr: str, metrics: list[str]) -> tuple[dict, list[str]]:
    strategies_used_queries = SideQueries.get_strategies_used_query(slr)
    check_review_query = SideQueries.get_check_review_query(slr)

    with Session() as session:
        strategies_used = get_strategies_used(
            strategies_used_queries, check_review_query, session
        )

        results: dict = {}
        strategies: list[str] = []

        for tes, sws in product(*strategies_used.values()):
            result_query: ResultQuery = ResultQuery(
                slr=slr,
                tes=tes,
                ews=sws,
                bonus_metrics=metrics,
            )

            queries = result_query.get_queries()

            results.update(get_results_from_db(queries, session))

            strategies.append(f"{tes}-{sws}")

        results.update(get_results_from_db(result_query.get_qgs_query(), session))

    return results, strategies


@app.command(help="Creates a Excel file based on the given Path and SLR.")
def save(
    path: Path = typer.Argument(
        ...,
        help="Path to the **folder** where the results Excel file should be saved.",
        dir_okay=True,
        exists=True,
    ),
    slr: str = typer.Argument(
        ..., help="Name of the SLR the results will be extracted."
    ),
    metrics: list[str] = typer.Option(
        default=None,
        help="Bonus metrics to order the results and generate bonus top 10 lists. "
        f"Available metrics: {[f'`{i}`' for i in _AVAILABLE_METRICS]} "
        f"(outside the defaults: {[f'`{i}`' for i in _DEFAULT_METRICS]})",
        show_default=False,
    ),
):
    verify_metrics(metrics)

    print("Retrieving information from database...")

    results, strategies = get_results(slr, metrics)

    excel_writer = pd.ExcelWriter(path / f"{slr}.xlsx", engine="xlsxwriter")

    save_xlsx(excel_writer, results, slr, strategies)
