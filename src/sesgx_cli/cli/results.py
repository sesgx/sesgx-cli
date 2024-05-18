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
from sesgx_cli.database.util.results_queries import ResultQuery

app = typer.Typer(rich_markup_mode="markdown", help="Get experiments' results.")


def _adjust_max_col_width(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str):
    for column in df:
        max_col_width = max(df[column].astype(str).map(len).max(), len(column))  # type: ignore
        col_idx = df.columns.get_loc(column)
        writer.sheets[sheet_name].set_column(col_idx, col_idx, max_col_width)
    writer.sheets[sheet_name].set_column(0, 0, 15)


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


def save_xlsx(
    excel_writer: pd.ExcelWriter,
    results: dict[str, dict],
    slr: str,
):
    with Progress() as progress:
        saving_progress = progress.add_task("[green]Saving...", total=len(results))
        with excel_writer:
            for i, (key, result) in enumerate(results.items()):
                df = pd.DataFrame(data=result["data"], columns=result["columns"])

                df.to_excel(excel_writer=excel_writer, sheet_name=key, index=False)
                _adjust_max_col_width(df, excel_writer, key)

                progress.update(
                    saving_progress,
                    description=f"[green]Saving {i + 1} of {len(results)}",
                    advance=1,
                    refresh=True,
                )

            _graph_tab(slr, excel_writer)

        progress.remove_task(saving_progress)


def get_results(slr: str) -> dict[str, dict]:
    strategies_used_queries = ResultQuery.get_strategies_used_query(slr)
    check_review_query = ResultQuery.get_check_review_query(slr)

    with Session() as session:
        strategies_used = get_strategies_used(
            strategies_used_queries, check_review_query, session
        )

        results: dict = {}

        for tes, wes in product(*strategies_used.values()):
            result_query: ResultQuery = ResultQuery(
                slr=slr,
                tes=tes,
                wes=wes,
            )

            stmt = result_query.get_queries()

            results.update(get_results_from_db(stmt, session))

        results.update(get_results_from_db(ResultQuery.get_qgs_query(slr), session))

    return results


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
):
    print("Retrieving information from database...")

    results = get_results(slr)

    excel_writer = pd.ExcelWriter(path / f"{slr}.xlsx", engine="xlsxwriter")

    save_xlsx(excel_writer, results, slr)
