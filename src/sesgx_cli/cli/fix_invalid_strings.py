import asyncio
from functools import wraps
from pathlib import Path

import typer
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import (
    SearchString,
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


app = AsyncTyper(
    rich_markup_mode="markdown", help="Fixes invalid strings in the database."
)


@app.async_command()
async def fix(
    config_file_path: Path = typer.Option(
        Path.cwd() / "config.toml",
        "--config-file-path",
        "-c",
        help="Path to the `config.toml` file.",
    ),
):
    """Fixes invalid strings in the database."""
    from scopus_client import InvalidStringError, ScopusClient

    config = ExperimentConfig.from_toml(config_file_path)

    with Session() as session:
        stmt = (
            select(SearchString)
            .join(SearchString.performance)
            .options(joinedload(SearchString.performance))
            .where(
                SearchStringPerformance.n_scopus_results == 0,
            )
            .order_by(SearchString.id)
        )

        search_strings = session.execute(stmt).scalars().all()

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
                total=len(search_strings),
            )

            for search_string in search_strings:
                try:
                    pages_iterator = client.search(search_string.string).__aiter__()

                    # since we only care if the string is invalid
                    # we can just fetch the first page
                    # and if it raises, we know it's invalid
                    await pages_iterator.__anext__()

                except InvalidStringError:
                    print(f"String with ID {search_string.id} is invalid.")

                    if search_string.performance:
                        search_string.performance.n_scopus_results = -1
                        session.add(search_string.performance)
                        session.commit()

                finally:
                    progress.advance(overall_task)

            progress.remove_task(overall_task)
