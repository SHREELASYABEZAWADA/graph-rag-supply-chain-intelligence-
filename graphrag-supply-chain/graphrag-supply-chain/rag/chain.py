"""LangChain-orchestrated RAG chain: hybrid-retrieve context, then prompt
the LLM to produce a source-aware, relationship-aware answer."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import settings
from retrieval.hybrid import HybridRetriever

SYSTEM_PROMPT = """You are a supply-chain intelligence assistant. You answer
questions using ONLY the graph and document context provided below. You
must:
- Trace multi-hop dependencies explicitly (supplier -> product -> warehouse -> customer).
- Cite the graph paths and/or document sources that support each claim.
- If the context does not contain enough information, say so plainly instead
  of guessing.
- Keep answers concise and structured: a direct answer first, then a
  "Sources" section listing the graph paths / documents used.
"""

USER_PROMPT = """Question: {question}

Context:
{context}

Answer the question using the context above. Include a "Sources" section."""


class SupplyChainRAGChain:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.llm = ChatOpenAI(
            model=settings.chat_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("user", USER_PROMPT)]
        )

    def ask(self, question: str, focus_entity: str | None = None) -> str:
        context = self.retriever.retrieve(question, focus_entity=focus_entity)
        messages = self.prompt.format_messages(
            question=question, context=context.to_prompt_context()
        )
        response = self.llm.invoke(messages)
        return response.content
