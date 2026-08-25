"""Ask a supply-chain question via the Graph RAG chain.

Usage:
    python scripts/ask.py "Which customers are exposed if Acme Metals has a shipping delay?"
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from rag.chain import SupplyChainRAGChain
from retrieval.graph_store import GraphStore
from retrieval.hybrid import HybridRetriever
from retrieval.vector_store import VectorStore


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ask.py "<question>"')
        sys.exit(1)

    question = sys.argv[1]

    graph_store = GraphStore()
    vector_store = VectorStore()
    retriever = HybridRetriever(graph_store, vector_store)
    chain = SupplyChainRAGChain(retriever)

    answer = chain.ask(question)
    print("\n" + answer + "\n")

    graph_store.close()


if __name__ == "__main__":
    main()
