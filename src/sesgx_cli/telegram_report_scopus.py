import os
from datetime import datetime

from telegram import Bot, ForumTopic

from sesgx_cli.env_vars import TELEGRAM_CHAT_ID_SCOPUS, TELEGRAM_TOKEN, USER_NAME


class TelegramReportScopus:
    def set_attrs(
        self,
        slr_name: str,
        experiment_name: str,
        n_strings: int,
    ):
        if os.environ.get("TELEGRAM_TOKEN") is not None:
            self._sesg_checkpoint_bot = Bot(token=TELEGRAM_TOKEN)
        else:
            self._sesg_checkpoint_bot = None

        self._chat_id = TELEGRAM_CHAT_ID_SCOPUS

        self.slr_name: str = slr_name
        self.experiment_name: str = experiment_name
        self.n_strings: int = n_strings

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

    async def _create_execution_report_topic_forum(self):
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
        await self._create_execution_report_topic_forum()

        message = (
            f"\U0001f7e2Starting <b>{self.experiment_name}</b> scopus search\U0001f7e2\n\n"
            f"<b>Total strings</b>: {self.n_strings}\n"
            f"<b>SLR</b>: {self.slr_name}\n"
            f"<b>Datetime</b>: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        )

        await self._sesg_checkpoint_bot.send_message(
            chat_id=self._chat_id,
            text=message,
            parse_mode="HTML",
            message_thread_id=self.message_thread_id,
        )

    async def send_progress_report(
        self,
        idx_string: int,
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
            f"\U0001f7e1Running <b>{idx_string}/{self.n_strings}</b>...\U0001f7e1\n\n"
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

    async def _close_execution_report_topic_forum(self):
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
            f"\U0001f534Finished <b>{self.experiment_name} scopus search</b> execution\U0001f534\n\n"
            f"<b>Total strings</b>: {self.n_strings}\n"
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

        await self._close_execution_report_topic_forum()

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
            f"\U00002757Error <b>{self.experiment_name} scopus search</b> execution\U00002757\n\n"
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
