from pathlib import Path

import typer
from rich import print

from sesgx_cli.database import Session
from sesgx_cli.database.models import SLR, SearchString

app = typer.Typer(
    rich_markup_mode="markdown",
    help="Render citation graphs. A node represents a paper, and the directed edge `A -> B` means that paper `A` **references** paper `B` (or that paper `B` is **cited by** paper `A`).",  # noqa: E501
)


@app.command()
def statistics(
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
):
    with Session() as session:
        slr = SLR.get_by_name(slr_name, session)

        number_of_components, mean_degree = slr.get_graph_statistics()

    print(f"Number of components: {number_of_components}")
    print(f"Mean degree: {mean_degree}")


@app.command()
def render_slr(
    out_path: Path = typer.Argument(
        ...,
        exists=False,
        file_okay=False,
        dir_okay=False,
        help="Path to the output file, without any extensions",
    ),
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
):
    from sesgx_cli.citation_graph import create_citation_graph

    with Session() as session:
        slr = SLR.get_by_name(slr_name, session)

        g = create_citation_graph(
            adjacency_list=slr.adjacency_list(use_node_id=True),
            studies_titles={s.node_id: s.title for s in slr.gs},
        )

        g.render(
            filename=out_path.stem + ".dot",
            directory=out_path.parent,
            format="pdf",
            view=True,
        )


@app.command()
def render_search_string(
    out_path: Path = typer.Argument(
        ...,
        exists=False,
        file_okay=False,
        dir_okay=False,
        help="Path to the output file, without any extensions",
    ),
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    search_string_id: int = typer.Argument(
        ...,
        help="Id of the search string to render",
    ),
):
    from sesgx_cli.citation_graph import create_citation_graph

    with Session() as session:
        search_string = SearchString.get_by_id(search_string_id, session)
        performance = search_string.performance

        if performance is None:
            print("The search string was not searched.")
            raise typer.Abort()

        slr = SLR.get_by_name(slr_name, session)

        g = create_citation_graph(
            adjacency_list=slr.adjacency_list(),
            studies_titles={s.node_id: s.title for s in slr.gs},
            start_set=[s.node_id for s in performance.gs_in_bsb],
        )

        g.attr(label=r"Dashed -> Not found\nBold -> Snowballing\nFilled -> Search")

        g.render(
            filename=out_path.stem + ".dot",
            directory=out_path.parent,
            format="pdf",
            view=True,
        )
