class StrategyBaseQueryNotImplemented(Exception):
    """There is no base query for the strategy provided."""


class ResultQuery:
    """Class for wrapping all the queries need to retrieve information from the experiments' results.

    Args:
        - slr (str): the SLR name;
        - ews (str): the enrichment word strategy;
        - tes (str): the topic extraction strategy;
        - bonus_metrics (list[str] | None): a list of bonus metrics to be added to the default ones;
        - row_num (int): the row number to be used in the top ten queries. QUERY NOT IN USE.
    """

    def __init__(
        self,
        slr: str,
        wes: str,
        tes: str,
        bonus_metrics: list[str] | None = None,
        row_num: int = 1,
    ):
        self._qgs_query: str = f"""
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

        self._results_queries: dict[str, str] = {
            f"lda-{wes}": f"""select distinct on (ssp.search_string_id) ssp.search_string_id,
                        ssp.start_set_precision,
                        ssp.start_set_recall,
                        ssp.start_set_f1_score,
                        ssp.bsb_recall,
                        ssp.sb_recall,
                        lp.min_document_frequency as min_df,
                        lp.n_topics as n_topics,
                        fp.n_enrichments_per_word as n_similar_w,
                        fp.n_words_per_topic as n_w_per_topic,
                        ssp.n_scopus_results as n_scopus_results,
                        ssp.n_qgs_in_scopus as n_qgs_studies_in_scopus,
                        ssp.n_gs_in_scopus as n_gs_studies_in_scopus,
                        e."name"
                    from search_string_performance ssp 
                        join params p on p.search_string_id = ssp.search_string_id 
                        join experiment e on e.id = p.experiment_id 
                        join slr s on s.id = e.slr_id 
                        join formulation_params fp on fp.id = p.formulation_params_id
                        left join lda_params lp on lp.id = p.lda_params_id
                    where s."name" = '{slr}' and p.word_enrichment_strategy = '{wes}'""",
            f"bt-{wes}": f"""select distinct on (ssp.search_string_id) ssp.search_string_id,
                        ssp.start_set_precision,
                        ssp.start_set_recall,
                        ssp.start_set_f1_score,
                        ssp.bsb_recall,
                        ssp.sb_recall,
                        bp.kmeans_n_clusters as n_clusters,
                        bp.umap_n_neighbors as n_neighbors,
                        fp.n_enrichments_per_word as n_similar_w,
                        fp.n_words_per_topic as n_w_per_topic,
                        ssp.n_scopus_results as n_scopus_results,
                        ssp.n_qgs_in_scopus as n_qgs_studies_in_scopus,
                        ssp.n_gs_in_scopus as n_gs_studies_in_scopus,
                        e."name"
                    from search_string_performance ssp 
                        join params p on p.search_string_id = ssp.search_string_id 
                        join experiment e on e.id = p.experiment_id 
                        join slr s on s.id = e.slr_id 
                        join formulation_params fp on fp.id = p.formulation_params_id
                        left join bertopic_params bp on bp.id = p.bertopic_params_id
                    where s."name" = '{slr}' and p.word_enrichment_strategy = '{wes}'""",
        }

        self._results_queries_by_row: dict[str, str] = {
            f"lda-{wes}": f"""select 
                            ssp.search_string_id as search_string_id,
                            ssp.start_set_precision,
                            ssp.start_set_recall,
                            ssp.start_set_f1_score,
                            ssp.bsb_recall,
                            ssp.sb_recall,
                            lp.min_document_frequency as min_df,
                            lp.n_topics as n_topics,
                            fp.n_enrichments_per_word as n_similar_w,
                            fp.n_words_per_topic as n_w_per_topic,
                            ssp.n_scopus_results as n_scopus_results,
                            ssp.n_qgs_in_scopus as n_qgs_studies_in_scopus,
                            ssp.n_gs_in_scopus as n_gs_studies_in_scopus,
                            e."name",
                            ROW_NUMBER() over (partition by e."name" order by ssp.{'placeholder'} desc) as row_num
                        from search_string_performance ssp 
                            join params p on p.search_string_id = ssp.search_string_id 
                            join experiment e on e.id = p.experiment_id 
                            join slr s on s.id = e.slr_id 
                            join formulation_params fp on fp.id = p.formulation_params_id
                            left join lda_params lp on lp.id = p.lda_params_id
                        where 
                            s."name" = '{slr}' and p.word_enrichment_strategy like '{wes}'""",
            f"bt-{wes}": f"""select
                            ssp.search_string_id as search_string_id,
                            ssp.start_set_precision,
                            ssp.start_set_recall,
                            ssp.start_set_f1_score,
                            ssp.bsb_recall,
                            ssp.sb_recall,
                            bp.kmeans_n_clusters as n_clusters,
                            bp.umap_n_neighbors as n_neighbors,
                            fp.n_enrichments_per_word as n_similar_w,
                            fp.n_words_per_topic as n_w_per_topic,
                            ssp.n_scopus_results as n_scopus_results,
                            ssp.n_qgs_in_scopus as n_qgs_studies_in_scopus,
                            ssp.n_gs_in_scopus as n_gs_studies_in_scopus,
                            e."name",
                            ROW_NUMBER() over (partition by e."name" order by ssp.{'placeholder'} desc) as row_num
                        from search_string_performance ssp 
                            join params p on p.search_string_id = ssp.search_string_id 
                            join experiment e on e.id = p.experiment_id 
                            join slr s on s.id = e.slr_id 
                            join formulation_params fp on fp.id = p.formulation_params_id
                            left join bertopic_params bp on bp.id = p.bertopic_params_id
                        where 
                            s."name" = '{slr}' and p.word_enrichment_strategy like '{wes}'""",
        }

        self._slr: str = slr
        self._row_num: int = row_num
        self.sws: str = wes
        self.tes: str = tes

        self._set_metrics(bonus_metrics)

    def _set_metrics(self, bonus_metrics: list[str] | None):
        self._metrics: list[str] = ["start_set_precision", "start_set_recall"]

        if bonus_metrics:
            self._metrics.extend(bonus_metrics)

    def _generate_top_ten_query(self, metric: str) -> str:
        """
        Generates queries for the top 10 best strings according to the strategy base query
        and the metric to order the results.

        Args:.
            metric: metrics available to order the results.

        Returns: the query added of the strategy base query as subquery, the order by and limit statements.

        """
        strategy_query = self._results_queries.get(f"{self.tes}-{self.sws}", None)

        if not strategy_query:
            raise StrategyBaseQueryNotImplemented()

        return (
            f"select * from ({strategy_query}) results "
            f"order by {metric} desc limit 10"
        )

    def get_queries(self) -> dict[str, str]:
        """
        Generates a dictionary with all the queries needed to compose the Excel file for analysis.

        Returns: A dict with the queries needed, they are:
            - {strategy}: all the {strategy} results;
            - qgs: all the experiments' QGSs;
            - top_ten_{strategy}_{metric}: top ten {strategy} results ordered by the {metric};

        """
        key: str = f"{self.tes}-{self.sws}"

        result_queries: dict = {}
        result_queries[key] = self._results_queries[key]

        if len(self.sws) > 4:
            sws_reduced_name = self.sws[:3]
        else:
            sws_reduced_name = self.sws

        if len(self.tes) > 4:
            tes_reduced_name = self.tes[:3]
        else:
            tes_reduced_name = self.tes

        for metric in self._metrics:
            metric_reduced_name = metric.replace("start_set_", "ss_")
            key: str = (
                f"t10_({tes_reduced_name}-{sws_reduced_name})_{metric_reduced_name}"
            )
            result_queries[key] = self._generate_top_ten_query(metric)

        return result_queries

    def get_qgs_query(self) -> dict[str, str]:
        return {"qgs": self._qgs_query}


class SideQueries:
    """Class with other queries related to the experiments' results."""

    @staticmethod
    def get_check_review_query(slr: str) -> str:
        check_review: str = f"""
        select
            case 
                when count(*)>0 then true
                else false
            end	
        from experiment e 
        join slr s on s.id = e.slr_id 
        where s."name" = '{slr}'
        """

        return check_review

    @staticmethod
    def get_strategies_used_query(slr: str) -> dict[str, str]:
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
