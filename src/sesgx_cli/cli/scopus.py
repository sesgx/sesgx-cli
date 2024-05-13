import asyncio
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from time import time
from typing import Callable

import typer
from rich import print
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from tenacity import retry, stop_after_attempt, wait_fixed

from sesgx_cli.async_typer import AsyncTyper
from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import (
    Experiment,
    SearchStringPerformance,
)
from sesgx_cli.experiment_config import ExperimentConfig
from sesgx_cli.telegram_report_scopus import TelegramReportScopus

telegram_report = TelegramReportScopus()


@dataclass
class AsyncElapsedTimer:
    timer_seconds: int = field(init=False, default=0)
    task: asyncio.Task | None = field(init=False, default=None)
    callback: Callable[[int], None]

    async def _timer(self):
        while True:
            self.callback(self.timer_seconds)
            await asyncio.sleep(1)
            self.timer_seconds += 1

    def start(self):
        self.task = asyncio.create_task(self._timer())

    def reset(self):
        self.timer_seconds = 0

    def stop(self):
        if self.task is not None:
            self.task.cancel()


def catch_exception():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as root_exception:
                try:
                    print(f"Root exception: {root_exception}")
                    await telegram_report.send_error_report(
                        error_message=str(root_exception)
                    )
                except Exception:
                    raise root_exception
                raise root_exception

        return wrapper

    return decorator


app = AsyncTyper(rich_markup_mode="markdown", help="Perform Scopus searches.")


@app.async_command()
@catch_exception()
@retry(stop=stop_after_attempt(5), wait=wait_fixed(5), reraise=True)
async def search(  # noqa: C901
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
    send_telegram_report: bool = typer.Option(
        False,
        "--telegram-report",
        "-tr",
        help="Send experiment report to telegram.",
        show_default=True,
    ),
):
    """Searches the strings of the experiment on Scopus."""
    start_time = time()
    from scopus_client import InvalidStringError, ScopusClient

    from sesgx_cli.evaluation_factory import EvaluationFactory, Study

    with Session() as session:
        experiment = Experiment.get_by_name(experiment_name, session)
        slr = experiment.slr

        config = ExperimentConfig.from_toml(config_file_path)

        print("Retrieving experiment search strings...")
        search_strings_list = experiment.get_search_strings_without_performance(session)
        n_strings = len(search_strings_list)

        if send_telegram_report:
            telegram_report.set_attrs(
                slr_name=slr.name,
                experiment_name=experiment.name,
                n_strings=n_strings,
            )

            if experiment.telegram_message_thread_id_scopus is None:
                await telegram_report.start_execution_report()
                experiment.telegram_message_thread_id_scopus = (
                    telegram_report.message_thread_id
                )

                session.add(experiment)
                session.commit()
                session.refresh(experiment)
            else:
                telegram_report.message_thread_id = (
                    experiment.telegram_message_thread_id_scopus
                )
                await telegram_report.resume_execution()

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
                total=n_strings,
            )

            for i, search_string in enumerate(search_strings_list):
                progress_task = progress.add_task(
                    "Paginating",
                )

                def timer_callback(seconds: int):
                    progress.update(
                        progress_task,
                        description=f"Elapsed {seconds} seconds",
                    )

                timer = AsyncElapsedTimer(
                    callback=timer_callback,
                )

                results: list[dict] = []

                try:
                    timer.start()

                    async for page in client.search(search_string.string):
                        progress.update(
                            progress_task,
                            total=page.n_pages,
                            advance=1,
                        )

                        results.extend(page.entries)
                        timer.reset()

                    evaluation = evaluation_factory.evaluate(
                        [r["dc:title"] for r in results if "dc:title" in r]
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
                    timer.stop()

                if send_telegram_report:
                    if i + 1 in (
                        1,  # 0% - of total params variations
                        int(n_strings * 0.25),  # 25%
                        int(n_strings * 0.50),  # 50%
                        int(n_strings * 0.75),  # 75%
                    ):
                        await telegram_report.send_progress_report(
                            idx_string=i + 1,
                            percentage=int(((i + 1) / n_strings) * 100)
                            if i != 0
                            else 0,
                            exec_time=time() - start_time,
                        )

            progress.remove_task(overall_task)

    if send_telegram_report:
        await telegram_report.send_finish_report(exec_time=time() - start_time)
