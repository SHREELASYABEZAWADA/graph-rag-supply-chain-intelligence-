"""Central configuration, loaded from environment variables / .env"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "supplychain123")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Vector store
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
    vector_collection_name: str = os.getenv("VECTOR_COLLECTION_NAME", "supply_chain_docs")

    # Retrieval tuning
    graph_traversal_depth: int = int(os.getenv("GRAPH_TRAVERSAL_DEPTH", "2"))
    top_k_vector: int = int(os.getenv("TOP_K_VECTOR", "5"))


settings = Settings()
