from itertools import product
from pathlib import Path
from random import sample

import typer
from rich import print
from rich.progress import Progress

from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import (
    SLR,
    Experiment,
    Params,
    SearchString,
)
from sesgx_cli.experiment_config import ExperimentConfig
from sesgx_cli.topic_extraction.strategies import TopicExtractionStrategy
from sesgx_cli.word_enrichment.strategies import WordEnrichmentStrategy

app = typer.Typer(
    rich_markup_mode="markdown",
    help="Start an experiment for a SLR. With multiple similar words generation strategies.",
)


@app.command()
def start(  # noqa: C901 - method too complex
    slr_name: str = typer.Argument(
        ...,
        help="Name of the Systematic Literature Review",
    ),
    experiment_name: str = typer.Argument(
        ...,
        help="Name of the new experiment.",
    ),
    config_toml_path: Path = typer.Option(
        Path.cwd() / "config.toml",
        "--config-toml-path",
        "-c",
        help="Path to a `config.toml` file.",
        dir_okay=False,
        file_okay=True,
        exists=True,
    ),
    topic_extraction_strategies_list: list[TopicExtractionStrategy] = typer.Option(
        [TopicExtractionStrategy.bertopic, TopicExtractionStrategy.lda],
        "--topic-extraction-strategy",
        "-tes",
        help="Which topic extraction strategies to use.",
    ),
    word_enrichment_strategies_list: list[WordEnrichmentStrategy] = typer.Option(
        [WordEnrichmentStrategy.bert, WordEnrichmentStrategy.mistral],
        "--word-enrichment-strategy",
        "-wes",
        help="Which word enrichment strategies to use.",
    ),
):
    """Starts an experiment and generates search strings.

    Will only generate strings using unseen parameters from the config file. If a string was already
    generated for this experiment using a set of parameters for the strategy, will skip it.
    """  # noqa: E501
    from sesgx import SeSG
    from transformers import logging  # type: ignore

    from sesgx_cli.string_formulation.scopus_string_formulation_model import (
        ScopusStringFormulationModel,
    )
    from sesgx_cli.word_enrichment.word_enrichment_cache import WordEnrichmentCache

    logging.set_verbosity_error()

    config = ExperimentConfig.from_toml(config_toml_path)

    with Session() as session:
        slr = SLR.get_by_name(slr_name, session)
        print(f"Found GS with size {len(slr.gs)}.")

        experiment = Experiment.get_or_create_by_name(
            name=experiment_name,
            slr_id=slr.id,
            session=session,
        )

        if experiment.id is None:
            qgs_size = len(slr.gs) // 3
            experiment.qgs = sample(slr.gs, k=qgs_size)

            session.add(experiment)
            session.commit()
            session.refresh(experiment)

        print(
            f"Creating QGS with size {len(experiment.qgs)} containing the following studies:"  # noqa: E501
        )
        for study in experiment.qgs:
            print(f'Study(id={study.id}, title="{study.title}")')

        print()

        docs = experiment.get_docs()
        enrichment_text = experiment.get_enrichment_text()

        if len(docs) < 10:
            print("[blue]Less than 10 documents. Duplicating the current documents.")
            print()
            docs = [*docs, *docs]

        print("Loading tokenizer and language model...")
        print()

        with Progress() as progress:
            for word_enrichment_strategy, topic_extraction_strategy in product(
                word_enrichment_strategies_list,
                topic_extraction_strategies_list,
            ):
                config_params_list = Params.create_with_strategy(
                    config=config,
                    experiment_id=experiment.id,
                    session=session,
                    word_enrichment_strategy=word_enrichment_strategy,
                    topic_extraction_strategy=topic_extraction_strategy,
                )

                n_params = len(config_params_list)
                progress_bar_task_id = progress.add_task(
                    f"Found [bright_cyan]{n_params}[/bright_cyan] parameters variations for {topic_extraction_strategy.value} with {word_enrichment_strategy.value}...",
                    # noqa: E501
                    total=n_params,
                )

                if word_enrichment_strategy == WordEnrichmentStrategy.bert:
                    from transformers import BertForMaskedLM, BertTokenizer

                    from sesgx_cli.word_enrichment.bert_strategy import (
                        BertWordEnrichmentStrategy,
                    )

                    # instead of using composition
                    # this part could be initialized by BertWordEnrichmentStrategy
                    bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
                    bert_model = BertForMaskedLM.from_pretrained("bert-base-uncased")
                    bert_model.eval()  # type: ignore

                    word_enrichment_model = BertWordEnrichmentStrategy(
                        enrichment_text=enrichment_text,
                        bert_model=bert_model,
                        bert_tokenizer=bert_tokenizer,
                    )

                elif isinstance(word_enrichment_strategy, WordEnrichmentStrategy):
                    from sesgx_cli.word_enrichment.llm_strategy import (
                        LLMWordEnrichmentStrategy,
                    )

                    word_enrichment_model = LLMWordEnrichmentStrategy(
                        enrichment_text=enrichment_text,
                        model=word_enrichment_strategy.value,
                    )

                else:
                    raise RuntimeError(
                        f"Invalid Similar Word Generation Strategy. Must be: {[e.value for e in WordEnrichmentStrategy]}."
                        # noqa: E501
                    )

                word_enrichment_model_with_cache = WordEnrichmentCache(
                    word_enrichment_model=word_enrichment_model,
                    word_enrichment_strategy=word_enrichment_strategy,
                    experiment_id=experiment.id,
                    session=session,
                )

                for i, params in enumerate(config_params_list):
                    progress.update(
                        progress_bar_task_id,
                        advance=1,
                        description=f"{topic_extraction_strategy.value} - {word_enrichment_strategy.value}: Using parameter variation [bright_cyan]{i + 1}[/] of [bright_cyan]{n_params}[/]",
                        # noqa: E501
                        refresh=True,
                    )

                    existing_params = Params.get_one_or_none(
                        experiment_id=params.experiment_id,
                        formulation_params_id=params.formulation_params_id,
                        word_enrichment_strategy=params.word_enrichment_strategy,
                        bertopic_params_id=params.bertopic_params_id,
                        lda_params_id=params.lda_params_id,
                        session=session,
                    )

                    if existing_params is not None:
                        progress.update(
                            progress_bar_task_id,
                            description=f"{topic_extraction_strategy.value} - {word_enrichment_strategy.value}: Skipped parameter variation [bright_cyan]{i + 1}[/] of [bright_cyan]{n_params}[/]",
                            # noqa: E501
                            refresh=True,
                        )
                        continue

                    if (
                        topic_extraction_strategy == TopicExtractionStrategy.bertopic
                        and params.bertopic_params is not None
                    ):
                        from sesgx_cli.topic_extraction.bertopic_strategy import (
                            BERTopicTopicExtractionStrategy,
                        )

                        topic_extraction_model = BERTopicTopicExtractionStrategy(
                            kmeans_n_clusters=params.bertopic_params.kmeans_n_clusters,
                            umap_n_neighbors=params.bertopic_params.umap_n_neighbors,
                        )

                    elif (
                        topic_extraction_strategy == TopicExtractionStrategy.lda
                        and params.lda_params is not None
                    ):
                        from sesgx_cli.topic_extraction.lda_strategy import (
                            LDATopicExtractionStrategy,
                        )

                        topic_extraction_model = LDATopicExtractionStrategy(
                            min_document_frequency=params.lda_params.min_document_frequency,
                            n_topics=params.lda_params.n_topics,
                        )

                    else:
                        raise RuntimeError(
                            "Invalid Topic Extraction Strategy or the params instance does not have neither a lda_params or bertopic_params"
                            # noqa: E501
                        )

                    formulation_params = params.formulation_params

                    string_formulation_model = ScopusStringFormulationModel(
                        use_enriched_string_formulation_model=formulation_params.n_enrichments_per_word
                        > 0,
                        min_year=slr.min_publication_year,
                        max_year=slr.max_publication_year,
                    )

                    sesg = SeSG(
                        topic_extraction_model=topic_extraction_model,
                        word_enrichment_model=word_enrichment_model_with_cache,
                        string_formulation_model=string_formulation_model,
                    )

                    string = sesg.generate(docs)

                    db_search_string = SearchString.get_or_create_by_string(
                        string,
                        session,
                    )

                    db_search_string.params_list.append(params)

                    session.add(db_search_string)
                    session.commit()

                progress.remove_task(progress_bar_task_id)
