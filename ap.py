
import streamlit as st
import pandas as pd
import json
import re
from openai import OpenAI
from neo4j import GraphDatabase
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from pydantic import BaseModel
from typing import List

# Streamlit Setup
st.set_page_config(page_title="HafiCare")

# Credentials
NEO4J_URI = "neo4j+s://70c9b926.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "k57UmjLJjIW21vGkcMbFAW8jEy4pq-YUpINF8oXqswI"
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

# Save doctor to Neo4j
def save_doctor_to_neo4j(doc):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run("""
            MERGE (d:Doctor {name: $name})
            SET d.description = $description,
                d.source_url = $source_url
            MERGE (s:Specialty {name: $specialty})
            MERGE (d)-[:HAS_SPECIALTY]->(s)
            MERGE (h:HealthCenter {name: $hospital})
            MERGE (d)-[:WORKS_AT]->(h)
        """, doc)
    driver.close()
    st.success(f" Doctor saved: {doc['name']}")


class OpenAIDoctorSearchResponseItem(BaseModel):
    name: str
    specialty: str
    hospital: str
    description: str
    source_url: str

class OpenAIDoctorSearchResponse(BaseModel):
    items: List[OpenAIDoctorSearchResponseItem]

# Web Search and Structured Extraction
def search_web_and_extract_doctors(question):
    web_response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{"role": "user", "content": question}]
    )
    content = web_response.choices[0].message.content
    st.markdown("**🌐 Web Search Result:**")
    st.markdown(content)

    extract_prompt = (
        "From the following text, extract ONLY a JSON list of doctors with these fields:"
        " name, specialty, hospital, description, source_url. Return ONLY a valid JSON array."
    )

    structured_response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": extract_prompt},
        {"role": "user", "content": content}
    ],
    response_format=OpenAIDoctorSearchResponse,
)
    
    # structured_response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": extract_prompt},
    #         {"role": "user", "content": content}
    #     ]
    # )
    raw_output = structured_response.choices[0].message.content
    st.code(raw_output, language="json")

    # Remove markdown formatting
    cleaned = re.sub(r"```json|```", "", raw_output).strip()

    try:
        doctors = json.loads(cleaned)
        return doctors
    except Exception as e:
        st.error(f"❌ JSON parsing error: {e}")
        return []

# Streamlit App UI
st.header("🧠 HafiCare: Real-Time Doctor Discovery")

question = st.text_input("Ask about doctors or health centers")

if question:
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

        chain = GraphCypherQAChain.from_llm(
            llm,
            graph=graph,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
            cypher_prompt_template="""
You are a Cypher assistant. Use this schema:
Nodes:
- Doctor(name, description, source_url)
- Specialty(name)
- HealthCenter(name)
Relationships:
- (Doctor)-[:HAS_SPECIALTY]->(Specialty)
- (Doctor)-[:WORKS_AT]->(HealthCenter)
"""
        )

        with st.spinner(" Searching Neo4j graph..."):
            result = chain(question)

        answer = result["result"]
        if not answer or any(x in answer.lower() for x in ["no data", "not found", "unable", "don't know"]):
            st.warning("No info in database. Searching the web...")
            doctors = search_web_and_extract_doctors(question)
            for doc in doctors:
                if all(k in doc for k in ["name", "specialty", "hospital"]):
                    doc.setdefault("description", "")
                    doc.setdefault("source_url", "")
                    save_doctor_to_neo4j(doc)
        else:
            st.success(" Found answer in Neo4j!")
            st.markdown(f"**Answer:** {answer}")
            st.code(result["intermediate_steps"], language="cypher")

    except Exception as e:
        st.error(f"❌ Error: {e}")


