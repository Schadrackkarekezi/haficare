from db.neo4j_interface import get_neo4j_driver
from llm.openai_model import generate_embedding, get_llm_model

DISCLAIMER_TEXT = (
    "This is not a substitute for professional medical advice. For demo purposes only. "
    "If symptoms are severe or you are concerned, please see a doctor."
)


def vector_search_conditions(symptoms: str, top_k: int = 3) -> list[dict]:
    vec = generate_embedding(symptoms)
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            results = session.run(
                """
                WITH $vec AS q
                CALL db.index.vector.queryNodes(
                  "conditionEmbeddingIndex",
                  $k,
                  q
                )
                YIELD node, score
                RETURN
                  node.symptom_summary AS symptom_summary,
                  node.possible_condition AS possible_condition,
                  node.advice AS advice,
                  node.urgency AS urgency,
                  score
                ORDER BY score DESC
                """,
                {"vec": vec, "k": top_k},
            )
            return [
                {
                    "symptom_summary": r["symptom_summary"],
                    "possible_condition": r["possible_condition"],
                    "advice": r["advice"],
                    "urgency": r["urgency"],
                    "score": r["score"],
                }
                for r in results
            ]
    finally:
        driver.close()


def get_diagnosis_from_symptoms(symptoms: str) -> dict:
    try:
        candidates = vector_search_conditions(symptoms)
    except Exception as e:
        return {
            "possible_conditions": [],
            "summary": f"Sorry, I couldn't look up possible conditions right now: {e}",
            "disclaimer": DISCLAIMER_TEXT,
        }

    if not candidates:
        return {
            "possible_conditions": [],
            "summary": "I couldn't find anything closely matching those symptoms in the reference data.",
            "disclaimer": DISCLAIMER_TEXT,
        }

    llm = get_llm_model()
    candidate_text = "\n".join(
        f"- {c['possible_condition']} (matches symptoms like: {c['symptom_summary']}; advice: {c['advice']}; urgency: {c['urgency']})"
        for c in candidates
    )
    prompt = (
        "A user described these symptoms: "
        f"\"{symptoms}\"\n\n"
        "Here are the closest matches from a reference symptom/condition knowledge base:\n"
        f"{candidate_text}\n\n"
        "Write a short (2-4 sentence), plain-language summary of the most likely possibilities and general advice. "
        "Do not present this as a confirmed diagnosis. Always recommend seeing a doctor for anything concerning."
    )
    response = llm.invoke(prompt)
    summary = getattr(response, "content", str(response))

    return {
        "possible_conditions": candidates,
        "summary": summary,
        "disclaimer": DISCLAIMER_TEXT,
    }
