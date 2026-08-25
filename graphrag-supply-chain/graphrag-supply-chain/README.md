# Graph RAG Supply Chain Intelligence

A Graph RAG (Retrieval-Augmented Generation) system that answers complex
supply-chain questions by combining:

- **Neo4j knowledge graph** — models suppliers, products, warehouses,
  shipments, and customers as nodes/relationships so multi-hop dependency
  questions ("which customers are exposed to Supplier X's shipping delays?")
  can be answered with graph traversal instead of guesswork.
- **Vector search** — embeds unstructured text (supplier notes, incident
  reports, contracts) for semantic similarity search.
- **Hybrid retriever** — merges vector hits with graph-expanded context
  (neighbors, paths, subgraphs) before handing everything to the LLM.
- **LangChain + OpenAI** — orchestrates retrieval and generates
  source-aware, relationship-aware answers.

## Architecture

```
                    ┌─────────────────────┐
                    │   User Question      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Hybrid Retriever    │
                    │  (retrieval/hybrid.py)│
                    └──────┬───────┬────────┘
                           │       │
              ┌────────────▼┐   ┌──▼─────────────┐
              │ Vector Store │   │  Neo4j Graph   │
              │ (Chroma)     │   │  Store         │
              │ semantic hit │   │  entity +      │
              │              │   │  N-hop expand  │
              └──────────────┘   └────────────────┘
                           │       │
                    ┌──────▼───────▼────────┐
                    │   Context Assembler    │
                    │  (dedupe, rank, cite)  │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   LLM (OpenAI via     │
                    │   LangChain)          │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Answer + Sources +   │
                    │  Graph Path Evidence  │
                    └───────────────────────┘
```

## Project layout

```
graphrag-supply-chain/
├── config.py                  # env-driven configuration
├── schema/
│   └── graph_schema.py        # node/relationship type definitions
├── ingestion/
│   ├── structured_loader.py   # CSV -> Neo4j (suppliers, products, etc.)
│   ├── entity_extractor.py    # LLM-based entity/relationship extraction
│   └── unstructured_loader.py # free-text docs -> graph + vector store
├── retrieval/
│   ├── graph_store.py         # Neo4j driver wrapper + Cypher queries
│   ├── vector_store.py        # embeddings + Chroma vector store
│   └── hybrid.py              # hybrid retriever combining both
├── rag/
│   └── chain.py                # LangChain RAG chain, prompt, Q&A
├── data/sample_data/           # example CSVs + incident notes
├── scripts/
│   ├── build_graph.py          # one-shot ingestion script
│   └── ask.py                  # CLI to ask questions
└── requirements.txt
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# start Neo4j (Docker) - or point to Neo4j Aura
docker run -d --name neo4j-supplychain \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/supplychain123 \
  neo4j:5

cp .env.example .env   # fill in NEO4J_URI / NEO4J_PASSWORD / OPENAI_API_KEY
```

## Build the graph + vector index

```bash
python scripts/build_graph.py
```

This loads `data/sample_data/*.csv` (structured entities/relationships) and
`data/sample_data/incident_notes.txt` (unstructured text), runs LLM-based
entity extraction on the unstructured content, writes everything into Neo4j,
and embeds text chunks into the Chroma vector store.

## Ask questions

```bash
python scripts/ask.py "Which customers are exposed if Supplier Acme Metals has a shipping delay?"
```

Example output:

```
Answer:
Three customers are exposed: Northwind Traders and Contoso Retail (both
sourced via Warehouse WH-12, which stocks products supplied by Acme Metals),
and Fabrikam Inc (indirect exposure via Product P-2004 which lists Acme
Metals as a secondary supplier).

Sources:
- Graph path: Acme Metals -[:SUPPLIES]-> P-1001 -[:STOCKED_IN]-> WH-12 -[:SHIPS_TO]-> Northwind Traders
- Graph path: Acme Metals -[:SUPPLIES]-> P-1001 -[:STOCKED_IN]-> WH-12 -[:SHIPS_TO]-> Contoso Retail
- Vector doc: incident_notes.txt#chunk_4 (Acme Metals port delay, Sept 2025)
```

## Notes on adapting this to real data

- Swap `data/sample_data/*.csv` for your ERP/WMS exports.
- `entity_extractor.py` uses an LLM prompt to pull entities/relationships out
  of free text (contracts, emails, incident reports) — tune the prompt/schema
  for your domain vocabulary.
- For production, add a re-ranking step and a graph-schema-aware Cypher
  generator (LangChain's `GraphCypherQAChain` or a custom function-calling
  layer) so the LLM can compose novel Cypher queries instead of relying only
  on pre-built traversal patterns.
