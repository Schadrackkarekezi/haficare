

import streamlit as st
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

from utils.credentials import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY
from db.neo4j_interface import upload_doctors_to_neo4j, upload_healthcenters_to_neo4j
from llm.prompts import SCHEMA_PROMPT
from llm.llm_interface import search_web

def run_app():
    st.set_page_config(page_title="HafiCare")
    st.title("HafiCare Diagnostic Assistant")

    # Load data
    df_hc = pd.read_csv("data/Rwanda_healthcenter.csv")
    df_doctors = pd.read_csv("data/Kigali_Doctors.csv").rename(columns={
        "Name": "name",
        "Specialty": "specialty",
        "Hospital": "hospital",
        "Description": "description"
    })

    # Upload button
    if st.button("Upload Data to Neo4j"):
        upload_healthcenters_to_neo4j(df_hc, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        upload_doctors_to_neo4j(df_doctors, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        st.success("Local data uploaded to Neo4j!")

    # QA Input
    st.header("Search Rwanda Health Info")
    question = st.text_input("Ask about doctors or health centers")

    if question:
        try:
            graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)
            llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

            chain = GraphCypherQAChain.from_llm(
                llm,
                graph=graph,
                verbose=True,
                return_intermediate_steps=True,
                allow_dangerous_requests=True,
                cypher_prompt_template=SCHEMA_PROMPT
            )

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
