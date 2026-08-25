"""Loads structured CSV exports (suppliers, products, warehouses, shipments,
customers, and their relationships) into the Neo4j graph."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from retrieval.graph_store import GraphStore


class StructuredLoader:
    def __init__(self, graph_store: GraphStore, data_dir: str | Path):
        self.graph_store = graph_store
        self.data_dir = Path(data_dir)

    def load_nodes(self, filename: str, label: str, id_column: str = "id"):
        path = self.data_dir / filename
        if not path.exists():
            print(f"  skip (not found): {path}")
            return
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            props = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
            self.graph_store.upsert_node(label, str(row[id_column]), props)
        print(f"  loaded {len(df)} {label} nodes")

    def load_relationships(
        self,
        filename: str,
        source_label: str,
        target_label: str,
        rel_type: str,
        source_col: str = "source_id",
        target_col: str = "target_id",
    ):
        path = self.data_dir / filename
        if not path.exists():
            print(f"  skip (not found): {path}")
            return
        df = pd.read_csv(path)
        prop_cols = [c for c in df.columns if c not in (source_col, target_col)]
        for _, row in df.iterrows():
            props = {c: row[c] for c in prop_cols if pd.notna(row[c])}
            self.graph_store.upsert_relationship(
                source_label, str(row[source_col]),
                target_label, str(row[target_col]),
                rel_type, props,
            )
        print(f"  loaded {len(df)} {rel_type} relationships")

    def load_all(self):
        print("Loading nodes...")
        self.load_nodes("suppliers.csv", "Supplier")
        self.load_nodes("products.csv", "Product")
        self.load_nodes("warehouses.csv", "Warehouse")
        self.load_nodes("customers.csv", "Customer")
        self.load_nodes("shipments.csv", "Shipment")

        print("Loading relationships...")
        self.load_relationships("supplies.csv", "Supplier", "Product", "SUPPLIES")
        self.load_relationships("stocked_in.csv", "Product", "Warehouse", "STOCKED_IN")
        self.load_relationships("ships_to.csv", "Warehouse", "Customer", "SHIPS_TO")
