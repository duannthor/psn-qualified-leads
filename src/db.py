import os
from neo4j import GraphDatabase


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")


_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    return _driver


def upsert_game(tx, title: str):
    tx.run(
        "MERGE (g:Game {title: $title})\n"
        "ON CREATE SET g.firstSeen = timestamp()\n"
        "SET g.lastSeen = timestamp()",
    title=title,
    )


def record_played_game(title: str):
    with get_driver().session() as session:
        session.execute_write(upsert_game, title)