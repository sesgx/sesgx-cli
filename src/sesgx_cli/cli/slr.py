from pathlib import Path

import typer
from rich import print
from rich.progress import Progress

from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import SLR, Study

app = typer.Typer(rich_markup_mode="markdown", help="Create a SLR.")


@app.command()
def create_from_json(
    json_file_path: Path = typer.Argument(
        ...,
        help="Path to a `slr.json` file.",
        dir_okay=False,
        file_okay=True,
        exists=True,
    ),
    txts_path: Path = typer.Argument(
        ...,
        help="Path to a folder with the studies text files.",
        dir_okay=True,
        file_okay=False,
        exists=True,
    ),
    txts_extension: str = typer.Option(
        "txt",
        "--extension",
        "-e",
        help="Extension of the text files (cermtxt, txt).",
    ),
):
    """Creates a SLR from a `.json` file, along with backward snowballing."""
    from fuzzy_bsb import (
        FuzzyBSBStudy,
        fuzzy_bsb,
    )

    slr = SLR.from_json(json_file_path)

    sb_studies: list[FuzzyBSBStudy] = []
    db_study_mapper: dict[int, Study] = {}

    for study in slr.gs:
        with open(
            txts_path / f"{study.node_id}.{txts_extension}",
            "r",
            encoding="utf-8",
        ) as f:
            text_content = f.read()

        sb_study = FuzzyBSBStudy(
            id=study.node_id,
            title=study.title,
            text_content=text_content,
        )

        db_study_mapper[study.node_id] = study
        sb_studies.append(sb_study)

    with Progress() as progress:
        snowballing_progress_task = progress.add_task(
            "[green]Snowballing...",
            total=len(sb_studies),
        )

        bsb_iterator = fuzzy_bsb(studies=sb_studies)
        for i, (study, references) in enumerate(bsb_iterator):
            db_study_mapper[study.id].references.extend(
                db_study_mapper[reference.id] for reference in references
            )

            progress.update(
                snowballing_progress_task,
                description=f"[green]Snowballing ({i + 1} of {len(sb_studies)})",
                advance=1,
                refresh=True,
            )

    with Session() as session:
        slr.gs = list(db_study_mapper.values())

        session.add(slr)
        session.commit()
        session.refresh(slr)

        print(
            f"Created {slr.to_string(['id', 'name', 'min_publication_year', 'max_publication_year'])}"  # noqa: E501
        )  # noqa: E501
