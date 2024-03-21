import asyncio
from functools import wraps
from pathlib import Path

import typer
from rich import print
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn

from sesgx_cli.async_typer import AsyncTyper
from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import (
    Experiment,
    SearchStringPerformance,
)
from sesgx_cli.experiment_config import ExperimentConfig


class AsyncTyper(typer.Typer):
    def async_command(self, *args, **kwargs):
        def decorator(async_func):
            @wraps(async_func)
            def sync_func(*_args, **_kwargs):
                return asyncio.run(async_func(*_args, **_kwargs))

            self.command(*args, **kwargs)(sync_func)
            return async_func

        return decorator


app = AsyncTyper(rich_markup_mode="markdown", help="Perform Scopus searches.")


@app.async_command()
async def search(
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the experiment to retrieve the search strings from.",
    ),
    config_file_path: Path = typer.Option(
        Path.cwd() / "config.toml",
        "--config-file-path",
        "-c",
        help="Path to the `config.toml` file.",
    ),
):
    """Searches the strings of the experiment on Scopus."""
    from scopus_client import InvalidStringError, ScopusClient

    from sesgx_cli.evaluation_factory import EvaluationFactory, Study

    with Session() as session:
        experiment = Experiment.get_by_name(experiment_name, session)
        slr = experiment.slr

        config = ExperimentConfig.from_toml(config_file_path)

        print("Retrieving experiment search strings...")
        search_strings_list = experiment.get_search_strings_without_performance(session)

        evaluation_gs = [
            Study(
                id=s.id,
                title=s.title,
                references=[Study(id=ref.id, title=ref.title) for ref in s.references],
            )
            for s in slr.gs
        ]

        evaluation_qgs = [
            Study(
                id=s.id,
                title=s.title,
                references=[Study(id=ref.id, title=ref.title) for ref in s.references],
            )
            for s in experiment.qgs
        ]

        evaluation_factory = EvaluationFactory(
            gs=evaluation_gs,
            qgs=evaluation_qgs,
        )

        client = ScopusClient(config.scopus_api_keys)

        with Progress(
            TextColumn(
                "[progress.description]{task.description}: {task.completed} of {task.total}"  # noqa: E501
            ),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            overall_task = progress.add_task(
                "Overall",
                total=len(search_strings_list),
            )

            for search_string in search_strings_list:
                progress_task = progress.add_task(
                    "Paginating",
                )

                results: list[dict] = []

                try:
                    async for page in client.search(search_string.string):
                        progress.update(
                            progress_task,
                            total=page.n_pages,
                            advance=1,
                        )

                        results.extend(page.entries)

                    evaluation = evaluation_factory.evaluate(
                        [r["dc:title"] for r in results]
                    )
                    performance = SearchStringPerformance.from_studies_lists(
                        n_scopus_results=len(results),
                        qgs_in_scopus=[
                            slr.get_study_by_id(s.id) for s in evaluation.qgs_in_scopus
                        ],
                        gs_in_scopus=[
                            slr.get_study_by_id(s.id) for s in evaluation.gs_in_scopus
                        ],
                        gs_in_bsb=[
                            slr.get_study_by_id(s.id) for s in evaluation.gs_in_bsb
                        ],
                        gs_in_sb=[
                            slr.get_study_by_id(s.id) for s in evaluation.gs_in_sb
                        ],
                        start_set_precision=evaluation.start_set_precision,
                        start_set_recall=evaluation.start_set_recall,
                        start_set_f1_score=evaluation.start_set_f1_score,
                        bsb_recall=evaluation.bsb_recall,
                        sb_recall=evaluation.sb_recall,
                        search_string_id=search_string.id,
                    )

                    session.add(performance)
                    session.commit()

                except InvalidStringError:
                    print("The following string raised an InvalidStringError")
                    print(search_string.string)

                    performance = SearchStringPerformance(
                        n_scopus_results=-1,
                        qgs_in_scopus=[],
                        gs_in_bsb=[],
                        gs_in_sb=[],
                        n_gs_in_scopus=0,
                        n_qgs_in_scopus=0,
                        gs_in_scopus=[],
                        n_gs_in_bsb=0,
                        n_gs_in_sb=0,
                        start_set_precision=0,
                        start_set_recall=0,
                        start_set_f1_score=0,
                        bsb_recall=0,
                        sb_recall=0,
                        search_string_id=search_string.id,
                    )

                    session.add(performance)
                    session.commit()

                finally:
                    progress.remove_task(progress_task)
                    progress.advance(overall_task)

            progress.remove_task(overall_task)
