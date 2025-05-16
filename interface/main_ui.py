import streamlit as st

from db.neo4j_interface import upload_doctors_to_neo4j, upload_healthcenters_to_neo4j, get_neo4j_graph
from llm.openai import search_web, get_llm_model
from llm.graph import get_graphqa_cypher_chain
from llm.prompts import SCHEMA_PROMPT


def run_app():
    st.set_page_config(page_title="HafiCare")
    st.title("HafiCare Diagnostic Assistant")

    # Upload button
    if st.button("Upload Data to Neo4j"):
        upload_healthcenters_to_neo4j()
        upload_doctors_to_neo4j()
        st.success("Local data uploaded to Neo4j!")

    # QA Input
    st.header("Search Rwanda Health Info")
    question = st.text_input("Ask about doctors or health centers")

    if question:
        try:
            graph = get_neo4j_graph()
            llm_model = get_llm_model()

            chain = get_graphqa_cypher_chain(llm_model=llm_model, graph=graph, prompt=SCHEMA_PROMPT)

            with st.spinner("Searching in graph..."):
                result = chain(question)

            graph_answer = result["result"]
            fallback_phrases = ["i don't know", "no data", "not found", "unable to answer", "couldn't find"]

            if not graph_answer or any(p in graph_answer.lower() for p in fallback_phrases):
                st.warning("No results found in the database. Searching the web...")
                with st.spinner("Searching the web..."):
                    web_result = search_web(question)
                    st.markdown(f"**Web Answer:** {web_result.content}")
            else:
                st.markdown(f"**Answer:** {graph_answer}")
                st.code(result["intermediate_steps"], language="cypher")

        except Exception as e:
            st.error(f"{e}")
