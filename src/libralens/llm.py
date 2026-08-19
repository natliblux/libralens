import os
from openai import OpenAI

from .constants import LLM_URL_ENV, LLM_MODEL_ENV, LLM_KEY_ENV

class LLM:

    def __init__(self):

        self.url = os.getenv(LLM_URL_ENV)
        self.model = os.getenv(LLM_MODEL_ENV)
        self.key = os.getenv(LLM_KEY_ENV)

        missing = []

        if not self.url:
            missing.append(LLM_URL_ENV)
        if not self.model:
            missing.append(LLM_MODEL_ENV)
        if missing:
            raise ValueError(f"missing llm environment variables: {', '.join(missing)}")

        self.client = OpenAI(base_url=self.url, api_key=self.key or "dummy")

    def run(self, system_prompt: str, user_prompt: str) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content