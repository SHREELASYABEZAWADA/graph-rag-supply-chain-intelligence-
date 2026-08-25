"""Uses the LLM to pull structured entities/relationships out of free text
(incident reports, emails, contracts) so they can be merged into the graph."""
from __future__ import annotations

import json

from langchain_openai import ChatOpenAI

from config import settings
from schema.graph_schema import EXTRACTION_SCHEMA_PROMPT


class EntityExtractor:
    def __init__(self):
        self._llm = ChatOpenAI(
            model=settings.chat_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    def extract(self, text: str) -> dict:
        prompt = f"{EXTRACTION_SCHEMA_PROMPT}\n\nText:\n\"\"\"\n{text}\n\"\"\""
        response = self._llm.invoke(prompt)
        raw = response.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON: {raw[:200]}") from exc

        parsed.setdefault("entities", [])
        parsed.setdefault("relationships", [])
        return parsed
