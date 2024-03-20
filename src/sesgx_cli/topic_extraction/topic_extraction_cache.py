import json
from dataclasses import dataclass
from typing import List

from sesgx import TopicExtractionModel
from sesgx_cli.database.models import (
    BERTopicParams,
    Experiment,
    LDAParams,
    TopicsExtractedCache,
)
from sesgx_cli.topic_extraction.strategies import TopicExtractionStrategy
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass
class TopicExtractionCache(TopicExtractionModel):
    topic_extraction_model: TopicExtractionModel
    topic_extraction_strategy: TopicExtractionStrategy
    experiment: Experiment
    n_words_per_topic: int
    session: Session
    topic_param: LDAParams | BERTopicParams

    def get_from_cache(self) -> list[list[str]] | None:
        if self.topic_extraction_strategy == TopicExtractionStrategy.lda:
            stmt = (select(TopicsExtractedCache.topics)
                    .where(TopicsExtractedCache.experiment_id == self.experiment.id)
                    .where(TopicsExtractedCache.lda_params_id == self.topic_param.id))
            
        elif self.topic_extraction_strategy == TopicExtractionStrategy.bertopic:
            stmt = (select(TopicsExtractedCache.topics)
                    .where(TopicsExtractedCache.experiment_id == self.experiment.id)
                    .where(TopicsExtractedCache.bertopic_params_id == self.topic_param.id))

        result = self.session.execute(stmt).scalar_one_or_none()
        
        if result is None:
            return None
        
        result = json.loads(result)
        
        result_parsed = [value for _, value in result.items()]

        return result_parsed

    def save_on_cache(self, topics: json) -> None:
        if self.topic_extraction_strategy == TopicExtractionStrategy.lda:
            s = TopicsExtractedCache(
                experiment_id=self.experiment.id,
                experiment=self.experiment,
                lda_params_id=self.topic_param.id,
                lda_params=self.topic_param,
                topics=topics,
            )
        elif self.topic_extraction_strategy == TopicExtractionStrategy.bertopic:
            s = TopicsExtractedCache(
                experiment=self.experiment,
                experiment_id=self.experiment.id,
                bertopic_params_id=self.topic_param.id,
                bertopic_params=self.topic_param,
                topics=topics,
            )

        self.session.add(s)
        self.session.commit()

    def extract(self, docs: list[str]) -> List[str]:
        topics = self.get_from_cache()
        
        if topics is None:
            topics = self.topic_extraction_model.extract(docs)            
            
            topics_dict = dict(enumerate(topics))            
            self.save_on_cache(json.dumps(topics_dict))
            
        topics_reduced = [topic[:self.n_words_per_topic] for topic in topics]        
        
        return topics_reduced