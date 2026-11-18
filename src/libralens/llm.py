import os
import time
from openai import OpenAI
from .constants import LLM_URL_ENV, LLM_MODEL_ENV, LLM_KEY_ENV, LLM_RPM_ENV, LLM_RETRIES_ENV

class LLM:

    def __init__(self):

        self.url = os.getenv(LLM_URL_ENV)
        self.model = os.getenv(LLM_MODEL_ENV)
        self.key = os.getenv(LLM_KEY_ENV)
        self.rpm = int(os.getenv(LLM_RPM_ENV, "0"))
        self.retries = int(os.getenv(LLM_RETRIES_ENV, "3"))

        missing = []

        if not self.url:
            missing.append(LLM_URL_ENV)
        if not self.model:
            missing.append(LLM_MODEL_ENV)
        if missing:
            raise ValueError(f"missing llm environment variables: {', '.join(missing)}")

        if self.rpm < 0 or self.retries < 0:
            raise ValueError("LLM RPM and retries must be non-negative")

        self.interval = 60 / self.rpm if self.rpm else 0
        self.next_request = 0.0

        self.client = OpenAI(
            base_url=self.url,
            api_key=self.key or "dummy",
            max_retries=self.retries
        )

    def run(self, system_prompt: str, user_prompt: str) -> str:

        if self.interval:
            now = time.monotonic()
            if now < self.next_request:
                time.sleep(self.next_request - now)
            self.next_request = time.monotonic() + self.interval

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content

    @staticmethod
    def is_configured() -> bool:
        return bool(os.getenv(LLM_URL_ENV) and os.getenv(LLM_MODEL_ENV))