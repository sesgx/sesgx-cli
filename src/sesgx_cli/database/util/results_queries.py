class StrategyBaseQueryNotImplemented(Exception):
    """There is no base query for the strategy provided."""


class ResultQuery:
    """Class for wrapping all the queries needed to retrieve information from the experiments' results.

    Args:
        - slr (str): the SLR name;
        - ews (str): the enrichment word strategy;
        - tes (str): the topic extraction strategy;
    """

    def __init__(self, slr: str, wes: str, tes: str):
        self._slr: str = slr
        self.wes: str = wes
        self.tes: str = tes

        self._results_queries: dict[str, str] = {
            f"lda-{self.wes}": f"""select
                                e."name",
                                ssp.search_string_id,
                                ssp.start_set_precision,
                                ssp.start_set_recall,
                                ssp.start_set_f1_score,
                                ssp.sb_recall,
                                ssp.bsb_recall,
                                ssp.n_scopus_results,
                                ssp.n_qgs_in_scopus,
                                ssp.n_gs_in_scopus,
                                ssp.n_gs_in_bsb,
                                ssp.n_gs_in_sb,
                                fp.n_enrichments_per_word,
                                fp.n_words_per_topic,
                                lp.min_document_frequency as min_df,
                                lp.n_topics
                            from search_string_performance ssp
                            left join params p on p.search_string_id = ssp.search_string_id
                            left join formulation_params fp on fp.id = p.formulation_params_id 
                            left join lda_params lp on lp.id = p.lda_params_id
                            left join experiment e on e.id = p.experiment_id
                            left join slr s on s.id = e.slr_id 
                            where s."name" = '{self._slr}' and p.word_enrichment_strategy = '{self.wes}'
                            order by p.id;""",
            f"bt-{self.wes}": f"""select
                                e."name",
                                ssp.search_string_id,
                                ssp.start_set_precision,
                                ssp.start_set_recall,
                                ssp.start_set_f1_score,
                                ssp.sb_recall,
                                ssp.bsb_recall,
                                ssp.n_scopus_results,
                                ssp.n_qgs_in_scopus,
                                ssp.n_gs_in_scopus,
                                ssp.n_gs_in_bsb,
                                ssp.n_gs_in_sb,
                                fp.n_enrichments_per_word,
                                fp.n_words_per_topic,
                                bp.kmeans_n_clusters,
                                bp.umap_n_neighbors 
                            from search_string_performance ssp
                            left join params p on p.search_string_id = ssp.search_string_id
                            left join formulation_params fp on fp.id = p.formulation_params_id 
                            left join bertopic_params bp on bp.id = p.bertopic_params_id 
                            left join experiment e on e.id = p.experiment_id
                            left join slr s on s.id = e.slr_id 
                            where s."name" = '{self._slr}' and p.word_enrichment_strategy = '{self.wes}'
                            order by p.id;""",
        }

    @staticmethod
    def get_strategies_used_query(slr: str) -> dict[str, str]:
        """Get the queries to retrieve the strategies used in the experiments.

        Args:
            - slr (str): the SLR name;
        """

        enrichment_strategies_query = f"""
        select 
            p.word_enrichment_strategy
        from params p 
        left join experiment e ON e.id = p.experiment_id 
        left join slr s on s.id = e.slr_id 
        where s."name" like '{slr}'
        group by p.word_enrichment_strategy;
        """

        topic_extract_strategies_query = f"""
        select 
            case 
                when count(p.lda_params_id) > 0 and count(p.bertopic_params_id) = 0 then 'lda'
                when count(p.bertopic_params_id) > 0 and count(p.lda_params_id) = 0 then 'bertopic'
                when count(p.lda_params_id) > 0 and count(p.bertopic_params_id) > 0 then 'lda, bertopic'
            end as topic_extraction_strategy
        from params p 
        left join experiment e ON e.id = p.experiment_id 
        left join slr s on s.id = e.slr_id 
        where s."name" like '{slr}'
        group by p.lda_params_id, p.bertopic_params_id
        limit 1; 
        """

        return {
            "tes": topic_extract_strategies_query,
            "sws": enrichment_strategies_query,
        }

    @staticmethod
    def get_check_review_query(slr: str) -> str:
        """Get the query to check if the review exists.

        Args:
            - slr (str): the SLR name;
        """
        check_review_query: str = f"""
        select 
            p.word_enrichment_strategy
        from params p 
        left join experiment e ON e.id = p.experiment_id 
        left join slr s on s.id = e.slr_id 
        where s."name" like '{slr}'
        group by p.word_enrichment_strategy;
        """

        return check_review_query

    @staticmethod
    def get_qgs_query(slr: str) -> dict[str, str]:
        """Get the query to retrieve the QGS used in each experiment.

        Args:
            - slr (str): the SLR name;
        """
        _qgs_query: str = f"""
        select 
            e."name", 
            s.id, 
            s.title
        from experiment_qgs eq 
        left join experiment e on e.id = eq.experiment_id 
        left join study s on s.id = eq.study_id 
        left join slr on slr.id = e.slr_id 
        where slr."name" = '{slr}';
        """
        return {"qgs": _qgs_query}

    def get_queries(self) -> dict[str, str]:
        """Get the queries to retrieve the results from each strategies used."""

        key: str = f"{self.tes}-{self.wes}"

        return {key: self._results_queries[key]}
