import os
from datetime import datetime

from telegram import Bot, ForumTopic

from sesgx_cli.env_vars import (
    PC_SPECS,
    TELEGRAM_CHAT_ID_EXPERIMENT,
    TELEGRAM_TOKEN,
    USER_NAME,
)
from sesgx_cli.topic_extraction.strategies import TopicExtractionStrategy
from sesgx_cli.word_enrichment.strategies import WordEnrichmentStrategy


class TelegramReportExperiment:
    def set_attrs(
        self,
        slr_name: str,
        experiment_name: str,
        topic_extraction_strategies_list: list[TopicExtractionStrategy],
        word_enrichment_strategies_list: list[WordEnrichmentStrategy],
    ):
        if os.environ.get("TELEGRAM_TOKEN") is not None:
            self._sesg_checkpoint_bot = Bot(token=TELEGRAM_TOKEN)
        else:
            self._sesg_checkpoint_bot = None

        self._chat_id = TELEGRAM_CHAT_ID_EXPERIMENT

        self.slr_name: str = slr_name
        self.experiment_name: str = experiment_name
        self.topic_extraction_strategies_list = topic_extraction_strategies_list
        self.word_enrichment_strategies_list = word_enrichment_strategies_list

    @staticmethod
    def get_execution_time(
        execution_time: float,
    ) -> tuple[int, int, int]:
        """
        Gets the hours, minutes and seconds of the given execution time in milliseconds
        for better visualization by the user.

        Args:
            execution_time: time passed in milliseconds.

        Returns: a tuple with hours, minutes and seconds converted.

        """
        hours = int(execution_time // 3600)
        minutes = int((execution_time % 3600) // 60)
        seconds = int(execution_time % 60)

        execution_time_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return execution_time_formatted

    async def create_execution_report_topic_forum(self):
        response: ForumTopic = await self._sesg_checkpoint_bot.create_forum_topic(
            chat_id=self._chat_id,
            name=f"{self.experiment_name} ({USER_NAME})",
            icon_custom_emoji_id="5417915203100613993",
        )

        self.message_thread_id = response.message_thread_id

    async def start_execution_report(self) -> None:
        """
        Report for a new experiment running. (`sesg experiment start`)
        """
        await self.create_execution_report_topic_forum()

        message = (
            f"\U0001f7e2Starting <b>{self.experiment_name}</b> execution\U0001f7e2\n\n"
            f"<b>Topic extraction</b>: {[item.value for item in self.topic_extraction_strategies_list]}\n"
            f"<b>Word enrichment</b>: {[item.value for item in self.word_enrichment_strategies_list]}\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
            f"<b>PC specs</b>: {PC_SPECS}"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

    async def start_execution_strategy_report(
        self,
        strategy: str,
    ) -> None:
        """
        Report for a new strategy starting its execution.

        Args:
            strategy: which strategy is starting. (e.g., lda, bertopic)
        """
        message = (
            f"\U0001f7e2Starting <b>{strategy}</b>\U0001f7e2\n\n"
            f"<b>Experiment</b>: {self.experiment_name}\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Percentage</b>: 0%\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

    async def send_progress_report(
        self,
        strategy: str,
        percentage: int,
        exec_time: float,
    ) -> None:
        """
        Report of the experiment progress (it's triggered every quarter of the total execution
        of each strategy).

        Args:
            strategy: which strategy is being executed.
            percentage: what percentage the execution at
            exec_time: total execution time passed.
        """
        execution_time = self.get_execution_time(exec_time)
        message = (
            f"\U0001f7e1Running <b>{strategy}</b>...\U0001f7e1\n\n"
            f"<b>Experiment</b>: {self.experiment_name}\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Percentage</b>: {percentage}%\n"
            f"<b>Current execution time</b>: {execution_time}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

    async def send_finish_strategy_report(
        self,
        exec_time: float,
        topic_extraction_strategy: TopicExtractionStrategy,
        word_enrichment_strategy: WordEnrichmentStrategy,
    ) -> None:
        """
        End of the execution report.

        Args:
            exec_time: total execution time passed.
        """
        execution_time = self.get_execution_time(exec_time)
        message = (
            f"\U00002705Finished <b>{topic_extraction_strategy.value} - {word_enrichment_strategy.value}</b> execution\U00002705\n\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Experiment</b>: {self.experiment_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
            f"<b>Execution total time</b>: {execution_time}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

    async def close_execution_report_topic_forum(self):
        await self._sesg_checkpoint_bot.edit_forum_topic(
            chat_id=self._chat_id,
            message_thread_id=self.message_thread_id,
            icon_custom_emoji_id="5237699328843200968",
        )

        await self._sesg_checkpoint_bot.close_forum_topic(
            chat_id=self._chat_id,
            message_thread_id=self.message_thread_id,
        )

    async def send_finish_report(
        self,
        exec_time: float,
    ) -> None:
        """
        End of the execution report.

        Args:
            exec_time: total execution time passed.
        """
        execution_time = self.get_execution_time(exec_time)
        message = (
            f"\U0001f534Finished <b>{self.experiment_name}</b> execution\U0001f534\n\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
            f"<b>Execution total time</b>: {execution_time}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

        await self.close_execution_report_topic_forum()

    async def send_error_report(
        self,
        error_message: str,
    ) -> None:
        """
        Error report.
        Args:
            error_message: error message raised.
        """
        message = (
            f"\U00002757Error <b>{self.experiment_name}</b> execution\U00002757\n\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
            f"<b>Error message</b>: {error_message}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

        await self._sesg_checkpoint_bot.edit_forum_topic(
            chat_id=self._chat_id,
            message_thread_id=self.message_thread_id,
            icon_custom_emoji_id="5379748062124056162",
        )

    async def resume_execution(self) -> None:
        """
        Resume the execution of the experiment.
        """
        message = (
            f"\U0001f4acResuming <b>{self.experiment_name}</b> execution\U0001f4ac\n\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

        try:
            await self._sesg_checkpoint_bot.edit_forum_topic(
                chat_id=self._chat_id,
                message_thread_id=self.message_thread_id,
                icon_custom_emoji_id="5417915203100613993",
            )
        except Exception:
            pass
