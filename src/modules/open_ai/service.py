import asyncio
from core.config import Config
from core.logger import logger


class OpenAIService:
    def __init__(self, config: Config):
        self.client = config.azure_client
        self.assistant_id = "asst_T5wYIPegTAqwxmf4ZcBrtehK"

    async def summarize_text(self, text: str) -> str:
        try:
            logger.info("Creating thread...")
            thread = self.client.beta.threads.create()

            logger.info("Adding message to thread...")
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Сделай краткий конспект следующего текста:\n\n{text}",
            )

            logger.info("Running assistant...")
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
            )

            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )

                if run.status in ("completed", "failed", "cancelled"):
                    break
                await asyncio.sleep(1)

            if run.status != "completed":
                logger.warning(f"Run ended with status={run.status}")
                return f"Ошибка: {run.status}"

            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            if not messages.data:
                return "Нет ответа от ассистента."

            latest = messages.data[0]
            text_content = latest.content[0].text.value if latest.content else ""
            return text_content.strip()

        except Exception as e:
            logger.exception("AI summarize_text failed")
            return f"Ошибка: {e}"
