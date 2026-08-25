"""
Defines the node labels, relationship types, and Cypher constraints for the
supply-chain knowledge graph.

Node labels:
    Supplier(id, name, region, tier, risk_score)
    Product(id, sku, name, category)
    Warehouse(id, name, region, capacity)
    Shipment(id, status, eta, origin, destination, carrier)
    Customer(id, name, region, segment)
    Incident(id, date, description, severity)   # extracted from unstructured text

Relationship types:
    (Supplier)-[:SUPPLIES {lead_time_days, cost}]->(Product)
    (Product)-[:STOCKED_IN {quantity}]->(Warehouse)
    (Warehouse)-[:SHIPS_TO]->(Customer)
    (Shipment)-[:CONTAINS]->(Product)
    (Shipment)-[:FROM_WAREHOUSE]->(Warehouse)
    (Shipment)-[:TO_CUSTOMER]->(Customer)
    (Incident)-[:AFFECTS]->(Supplier | Warehouse | Shipment)
"""

NODE_LABELS = [
    "Supplier",
    "Product",
    "Warehouse",
    "Shipment",
    "Customer",
    "Incident",
]

RELATIONSHIP_TYPES = [
    "SUPPLIES",       # Supplier -> Product
    "STOCKED_IN",      # Product -> Warehouse
    "SHIPS_TO",        # Warehouse -> Customer
    "CONTAINS",        # Shipment -> Product
    "FROM_WAREHOUSE",  # Shipment -> Warehouse
    "TO_CUSTOMER",     # Shipment -> Customer
    "AFFECTS",         # Incident -> any node
]

# Cypher statements to enforce uniqueness on primary IDs. Run once at setup.
CONSTRAINT_STATEMENTS = [
    "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.id IS UNIQUE",
    "CREATE CONSTRAINT shipment_id IF NOT EXISTS FOR (sh:Shipment) REQUIRE sh.id IS UNIQUE",
    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
]

# JSON-schema-like structure handed to the LLM during extraction so it
# returns entities/relationships the ingestion pipeline can parse reliably.
EXTRACTION_SCHEMA_PROMPT = """
Extract supply-chain entities and relationships from the text below.
Return ONLY valid JSON matching this shape (no markdown fences, no prose):

{
  "entities": [
    {"id": "string-unique-slug", "label": "Supplier|Product|Warehouse|Shipment|Customer|Incident",
     "properties": {"name": "string", "...": "..."}}
  ],
  "relationships": [
    {"source_id": "string", "target_id": "string", "type": "SUPPLIES|STOCKED_IN|SHIPS_TO|CONTAINS|FROM_WAREHOUSE|TO_CUSTOMER|AFFECTS",
     "properties": {}}
  ]
}

Rules:
- Reuse the same id for an entity if it is mentioned more than once.
- Only use the node labels and relationship types listed above.
- If a property is unknown, omit it rather than guessing.
"""
