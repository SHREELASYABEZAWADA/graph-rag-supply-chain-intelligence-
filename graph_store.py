"""Thin wrapper around the Neo4j driver: writes + graph-traversal reads."""
from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase

from config import settings


class GraphStore:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self._driver.close()

    def run(self, cypher: str, **params) -> list[dict[str, Any]]:
        with self._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, **params)
            return [record.data() for record in result]

    def apply_constraints(self, statements: list[str]):
        for stmt in statements:
            self.run(stmt)

    def upsert_node(self, label: str, node_id: str, properties: dict[str, Any]):
        cypher = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $props
        """
        self.run(cypher, id=node_id, props=properties)

    def upsert_relationship(
        self,
        source_label: str,
        source_id: str,
        target_label: str,
        target_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ):
        cypher = f"""
        MATCH (a:{source_label} {{id: $source_id}})
        MATCH (b:{target_label} {{id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props
        """
        self.run(cypher, source_id=source_id, target_id=target_id, props=properties or {})

    # ---- Read patterns used by the hybrid retriever -----------------

    def find_entity_by_name(self, name_fragment: str, limit: int = 5) -> list[dict]:
        """Fuzzy match a node by name across all supply-chain labels."""
        cypher = """
        MATCH (n)
        WHERE any(l IN labels(n) WHERE l IN
              ['Supplier','Product','Warehouse','Shipment','Customer','Incident'])
          AND toLower(n.name) CONTAINS toLower($fragment)
        RETURN labels(n) AS labels, n AS node
        LIMIT $limit
        """
        return self.run(cypher, fragment=name_fragment, limit=limit)

    def expand_neighborhood(self, node_id: str, depth: int = 2, limit: int = 25) -> list[dict]:
        """
        N-hop traversal from a node, returning readable paths so the LLM can
        cite exact relationship chains (e.g. Supplier -> Product -> Warehouse
        -> Customer) as evidence.
        """
        cypher = f"""
        MATCH path = (start {{id: $node_id}})-[*1..{depth}]-(neighbor)
        RETURN
            [node IN nodes(path) | coalesce(node.name, node.id)] AS path_nodes,
            [rel IN relationships(path) | type(rel)] AS path_rels
        LIMIT $limit
        """
        return self.run(cypher, node_id=node_id, limit=limit)

    def find_dependency_chain(self, supplier_name: str) -> list[dict]:
        """
        Common supply-chain question pattern: 'who is exposed if Supplier X
        has a problem?' Traces Supplier -> Product -> Warehouse -> Customer.
        """
        cypher = """
        MATCH (s:Supplier)-[:SUPPLIES]->(p:Product)-[:STOCKED_IN]->(w:Warehouse)-[:SHIPS_TO]->(c:Customer)
        WHERE toLower(s.name) CONTAINS toLower($supplier_name)
        RETURN s.name AS supplier, p.name AS product, w.name AS warehouse, c.name AS customer
        """
        return self.run(cypher, supplier_name=supplier_name)

    def find_related_incidents(self, entity_name: str) -> list[dict]:
        cypher = """
        MATCH (i:Incident)-[:AFFECTS]->(n)
        WHERE toLower(n.name) CONTAINS toLower($entity_name) OR toLower(n.id) CONTAINS toLower($entity_name)
        RETURN i.description AS description, i.date AS date, i.severity AS severity, n.name AS affected
        """
        return self.run(cypher, entity_name=entity_name)
