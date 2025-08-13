from db.neo4j_interface import get_neo4j_driver
from llm.openai_model import generate_embedding

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
            RETURN
              node.name AS name,
              node.specialty AS specialty,
              node.location AS location,
              score
            ORDER BY score DESC
            """,
            {"vec": vec, "k": top_r}
        )
        doctors = [
            {
                "name": r["name"],
                "specialty": r["specialty"],
                "score": r["score"],
            }
            for r in results
        ]
    driver.close()
    return doctors


def find_doctors_by_question(query: str) -> str:
    try:
        matches = vector_search_doctors(query)
        if not matches:
            return "Sorry, I couldn't find any doctors matching your request."

        result = "**Here are some doctors I found:**\n"
        for i, doc in enumerate(matches, 1):
            result += f"{i}. **{doc['name']}** — *{doc['specialty']}* (Score: {doc['score']:.2f})\n"
        return result
    except Exception as e:
        return f"Error during doctor search: {e}"
