
from db.neo4j_interface import get_neo4j_graph
from llm.graph import get_graphqa_cypher_chain
from llm.prompts import SCHEMA_PROMPT
from llm.openai_model import get_llm_model

def find_doctors_by_question(question: str) -> str:
# finding the doctor from neo4j 
    try:
        graph = get_neo4j_graph()
        llm = get_llm_model()
        chain = get_graphqa_cypher_chain(llm_model=llm, graph=graph, prompt=SCHEMA_PROMPT)
        result = chain(question)
        return result.get("result", "No result found.")
    except Exception as e:
        return f"Error during doctor search: {e}"



