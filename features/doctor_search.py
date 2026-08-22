import numpy as np

from db.neo4j_interface import get_neo4j_driver
from llm.openai_model import generate_embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def vector_search_doctors(query: str, top_r: int = 2):
    vec = generate_embedding(query)
    driver = get_neo4j_driver()
    with driver.session() as session:
        results = session.run(
            """
            WITH $vec AS q
            CALL db.index.vector.queryNodes(
              "doctorEmbeddingIndex",
              $k,
              q
            )
            YIELD node, score
            OPTIONAL MATCH (node)-[:HAS_SPECIALTY]->(s:Specialty)
            OPTIONAL MATCH (node)-[:WORKS_AT]->(h:HealthCenter)
            RETURN
              node.name AS name,
              s.name AS specialty,
              h.name AS hospital,
              score
            ORDER BY score DESC
            """,
            {"vec": vec, "k": top_r}
        )
        doctors = [
            {
                "name": r["name"],
                "specialty": r["specialty"],
                "hospital": r["hospital"],
                "score": r["score"],
            }
            for r in results
        ]
    driver.close()
    return doctors


def vector_search_doctors_for_clinic(query: str, clinic_id: int, top_r: int = 3):
    """Clinic-scoped doctor search.

    Deliberately does NOT filter the ANN vector index by clinic_id: that index
    ranks across every clinic combined and only filters afterward, so a small
    clinic's doctors can fall outside the global top-k and searches return
    empty even when a real match exists. Instead this fetches the clinic's
    (realistically small) doctor roster directly and ranks it with cosine
    similarity in Python. Revisit if a single clinic's roster grows into the
    hundreds.
    """
    query_vec = generate_embedding(query)
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            rows = session.run(
                """
                MATCH (d:Doctor {clinic_id: $clinic_id, is_active: true})
                OPTIONAL MATCH (d)-[:HAS_SPECIALTY]->(s:Specialty)
                RETURN
                  d.postgres_doctor_id AS doctor_id,
                  d.name AS name,
                  s.name AS specialty,
                  d.embedding AS embedding
                """,
                {"clinic_id": clinic_id},
            )
            candidates = [dict(r) for r in rows]
    finally:
        driver.close()

    scored = [
        {
            "doctor_id": c["doctor_id"],
            "name": c["name"],
            "specialty": c["specialty"],
            "score": _cosine_similarity(query_vec, c["embedding"]),
        }
        for c in candidates
        if c.get("embedding")
    ]
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[:top_r]
