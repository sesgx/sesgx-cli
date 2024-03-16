from itertools import product
from pathlib import Path
from random import sample
from time import time

import typer
from rich import print
from rich.progress import Progress

from sesgx_cli.database.connection import Session
from sesgx_cli.database.models import (
    SLR,
    BERTopicParams,
    Experiment,
    FormulationParams,
    LDAParams,
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
    send_telegram_report: bool = typer.Option(
        False,
        "--telegram-report",
        "-tr",
        help="Send experiment report to telegram.",
        show_default=True,
    )
):
    """Starts an experiment and generates search strings.

    Will only generate strings using unseen parameters from the config file. If a string was already
    generated for this experiment using a set of parameters for the strategy, will skip it.
    """  # noqa: E501
    start_time = time()
    from sesgx import SeSG
    from transformers import logging  # type: ignore

    from sesgx_cli.string_formulation.scopus_string_formulation_model import (
        ScopusStringFormulationModel,
    )
    from sesgx_cli.word_enrichment.word_enrichment_cache import WordEnrichmentCache

    logging.set_verbosity_error()

    config = ExperimentConfig.from_toml(config_toml_path)

    if send_telegram_report:
        from sesgx_cli.telegram_report import TelegramReport
        telegram_report = TelegramReport(
            slr_name=slr_name,
            experiment_name=experiment_name,
            strategies=list(product([s.value for s in topic_extraction_strategies_list],
                                    [s.value for s in word_enrichment_strategies_list])),
        )

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

        if send_telegram_report:
            telegram_report.send_new_execution_report()

        with Progress() as progress:
            print("Retrieving strategies parameters from database...")
            bertopic_params = BERTopicParams.get_or_save_from_params_product(
                kmeans_n_clusters_list=config.bertopic_params.kmeans_n_clusters,
                umap_n_neighbors_list=config.bertopic_params.umap_n_neighbors,
                session=session,
            )

            lda_params = LDAParams.get_or_save_from_params_product(
                min_document_frequency_list=config.lda_params.min_document_frequency,
                n_topics_list=config.lda_params.n_topics,
                session=session,
            )

            formulation_params = FormulationParams.get_or_save_from_params_product(
                n_enrichments_per_word_list=config.formulation_params.n_enrichments_per_word,
                n_words_per_topic_list=config.formulation_params.n_words_per_topic,
                session=session,
            )

            for word_enrichment_strategy, topic_extraction_strategy in product(
                word_enrichment_strategies_list,
                topic_extraction_strategies_list,
            ):
                if topic_extraction_strategy == TopicExtractionStrategy.bertopic:
                    concatenated_params = product(bertopic_params, formulation_params)
                elif topic_extraction_strategy == TopicExtractionStrategy.lda:
                    concatenated_params = product(lda_params, formulation_params)
                else:
                    raise RuntimeError(
                        "Invalid Topic Extraction Strategy or the params instance does not have neither a lda_params or bertopic_params"
                        # noqa: E501
                    )

                concatenated_params = list(concatenated_params)

                n_params = len(concatenated_params)
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

                for i, (topic_param, formulation_param) in enumerate(
                    concatenated_params
                ):
                    progress.update(
                        progress_bar_task_id,
                        advance=1,
                        description=f"{topic_extraction_strategy.value} - {word_enrichment_strategy.value}: Using parameter variation [bright_cyan]{i + 1}[/] of [bright_cyan]{n_params}[/]",
                        # noqa: E501
                        refresh=True,
                    )

                    word_enrichment_model_with_cache = WordEnrichmentCache(
                        word_enrichment_model=word_enrichment_model,
                        word_enrichment_strategy=word_enrichment_strategy,
                        experiment=experiment,
                        session=session,
                        n_enrichments=formulation_param.n_enrichments_per_word,
                    )

                    current_concatenated_params = Params.get_one_or_none(
                        experiment_id=experiment.id,
                        formulation_params_id=formulation_param.id,
                        topic_extraction_strategy=topic_extraction_strategy,
                        word_enrichment_strategy=word_enrichment_strategy.value,
                        bertopic_params_id=topic_param.id,
                        lda_params_id=topic_param.id,
                        session=session,
                    )

                    if send_telegram_report and i+1 in (n_params*0.25, n_params*0.50, n_params*0.75):
                        telegram_report.send_progress_report(strategy=f"{topic_extraction_strategy.value} - {word_enrichment_strategy.value}",
                                                             percentage=int(
                                                                 ((i+1)/n_params)*100),
                                                             exec_time=time()-start_time)

                    if current_concatenated_params is not None:
                        progress.update(
                            progress_bar_task_id,
                            description=f"{topic_extraction_strategy.value} - {word_enrichment_strategy.value}: Skipped parameter variation [bright_cyan]{i + 1}[/] of [bright_cyan]{n_params}[/]",
                            # noqa: E501
                            refresh=True,
                        )
                        continue

                    if (
                        topic_extraction_strategy == TopicExtractionStrategy.bertopic
                        and isinstance(topic_param, BERTopicParams)
                    ):
                        from sesgx_cli.topic_extraction.bertopic_strategy import (
                            BERTopicTopicExtractionStrategy,
                        )

                        topic_extraction_model = BERTopicTopicExtractionStrategy(
                            kmeans_n_clusters=topic_param.kmeans_n_clusters,
                            umap_n_neighbors=topic_param.umap_n_neighbors,
                        )

                    elif (
                        topic_extraction_strategy == TopicExtractionStrategy.lda
                        and isinstance(topic_param, LDAParams)
                    ):
                        from sesgx_cli.topic_extraction.lda_strategy import (
                            LDATopicExtractionStrategy,
                        )

                        topic_extraction_model = LDATopicExtractionStrategy(
                            min_document_frequency=topic_param.min_document_frequency,
                            n_topics=topic_param.n_topics,
                        )

                    else:
                        raise RuntimeError(
                            "Invalid Topic Extraction Strategy or the params instance does not have neither a lda_params or bertopic_params"
                            # noqa: E501
                        )

                    string_formulation_model = ScopusStringFormulationModel(
                        use_enriched_string_formulation_model=formulation_param.n_enrichments_per_word
                        > 0,
                        min_year=slr.min_publication_year,
                        max_year=slr.max_publication_year,
                        n_words_per_topic=formulation_param.n_words_per_topic,
                    )

                    sesg = SeSG(
                        topic_extraction_model=topic_extraction_model,
                        word_enrichment_model=word_enrichment_model_with_cache,
                        string_formulation_model=string_formulation_model,
                    )

                    print("generating string...")
                    string = sesg.generate(docs)
                    print("generated string")

                    db_search_string = SearchString.get_or_save_by_string(
                        string,
                        session,
                    )

                    if (
                        topic_extraction_strategy == TopicExtractionStrategy.lda
                        and isinstance(topic_param, LDAParams)
                    ):
                        concatenated_params = Params(
                            experiment_id=experiment.id,
                            experiment=experiment,
                            lda_params_id=topic_param.id,
                            lda_params=topic_param,
                            formulation_params_id=formulation_param.id,
                            formulation_params=formulation_param,
                            word_enrichment_strategy=word_enrichment_strategy.value,
                            search_string_id=db_search_string.id,
                            search_string=db_search_string,
                        )

                    elif (
                        topic_extraction_strategy == TopicExtractionStrategy.bertopic
                        and isinstance(topic_param, BERTopicParams)
                    ):
                        concatenated_params = Params(
                            experiment_id=experiment.id,
                            experiment=experiment,
                            bertopic_params_id=topic_param.id,
                            bertopic_params=topic_param,
                            formulation_params_id=formulation_param.id,
                            formulation_params=formulation_param,
                            word_enrichment_strategy=word_enrichment_strategy.value,
                            search_string_id=db_search_string.id,
                            search_string=db_search_string,
                        )
                    else:
                        raise RuntimeError(
                            "Invalid Topic Extraction Strategy or the params instance does not have neither a lda_params or bertopic_params"
                            # noqa: E501
                        )

                    session.add(concatenated_params)
                    session.commit()

                progress.remove_task(progress_bar_task_id)

    if send_telegram_report:
        telegram_report.send_finish_report(exec_time=time()-start_time)
