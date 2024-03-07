from pathlib import Path

import typer

from sesgx_cli.experiment_config import ExperimentConfig

app = typer.Typer(rich_markup_mode="markdown", help="Create the `config.toml` file.")


@app.command()
def init(
    path: Path = typer.Argument(
        Path.cwd() / "config.toml",
        help="Path to where the configuration file will be created.",  # noqa: E501
        dir_okay=False,
        file_okay=False,
        exists=False,
    ),
):
    """Initializes a `config.toml` file."""
    default_config = ExperimentConfig.create_default()

    default_config.to_toml(path)


if __name__ == "__main__":
    app()
