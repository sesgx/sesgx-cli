from pathlib import Path

import typer
from rich.progress import Progress

app = typer.Typer(rich_markup_mode="markdown", help="Convert pdfs to txt.")


@app.command()
def convert(
    pdfs_folder_path: Path = typer.Argument(
        ...,
        help="Path to the pdfs folder that will be converted.",
        dir_okay=True,
        exists=True,
    ),
):
    import PyPDF2

    files: list[Path] = list(pdfs_folder_path.iterdir())

    txts_folder_path: Path = pdfs_folder_path.parent.joinpath("txts")
    txts_folder_path.mkdir(parents=True, exist_ok=True)

    with Progress() as progress:
        convertion_progress = progress.add_task(
            "[green]Converting...", total=len(files)
        )
        for idx, file in enumerate(files):
            paper_id: str = file.stem
            text = ""

            with open(file, "rb") as pdf:
                try:
                    reader: PyPDF2.PdfReader = PyPDF2.PdfReader(pdf)

                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        text += page.extract_text()

                except Exception as e:
                    print(f"File: {file}\nError: {e}")

                with open(
                    txts_folder_path.joinpath(f"{paper_id}.txt"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(text)

            progress.update(
                convertion_progress,
                description=f"[green]Converting {idx+1} of {len(files)}",
                advance=1,
                refresh=True,
            )
