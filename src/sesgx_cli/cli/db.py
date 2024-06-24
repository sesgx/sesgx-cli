import typer

from sesgx_cli.database.connection import engine
from sesgx_cli.database.models.base import Base
from sesgx_cli.env_vars import DATABASE_URL

app = typer.Typer(rich_markup_mode="markdown", help="Create or drop the database.")


@app.command()
def create_tables():
    """Creates the tables on the database."""
    typer.confirm(
        f"Database in use: {DATABASE_URL}. Confirm?",
        default=False,
        abort=True,
    )
    Base.metadata.create_all(bind=engine)


@app.command()
def drop_tables():
    """Drops the tables from the database."""
    typer.confirm(
        f"Database in use: {DATABASE_URL}. Confirm?",
        default=False,
        abort=True,
    )
    confirmed = typer.confirm(
        "Are you sure you want to drop the database?", default=False
    )

    if not confirmed:
        raise typer.Abort()

    Base.metadata.drop_all(bind=engine)
