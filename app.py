import streamlit as st
import pandas as pd
from openai import OpenAI  
from neo4j import GraphDatabase
from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

# Streamlit page config
st.set_page_config(page_title="HafiCare")

# Credentials
NEO4J_URI = "neo4j+s://70c9b926.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "k57UmjLJjIW21vGkcMbFAW8jEy4pq-YUpINF8oXqswI"
OPENAI_API_KEY = "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"

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# File paths
healthcenter_path = "C:/Users/vital/Documents/research/Rwanda_heahthcenter.csv"
doctor_path = "C:/Users/vital/Documents/research/Kigali_Doctors.csv"

# Load CSV data
df_hc = pd.read_csv(healthcenter_path)
df_doctors = pd.read_csv(doctor_path).rename(columns={
    "Name": "name",
    "Specialty": "specialty",
    "Hospital": "hospital",
    "Description": "description"
})

# Function to upload health centers to Neo4j
def upload_healthcenters_to_neo4j(df, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        for _, row in df.iterrows():
            session.run(
                """
                MERGE (c:Country {name: $country})
                MERGE (a:Admin1 {name: $province})
                MERGE (ft:FacilityType {name: $type})
                MERGE (o:Ownership {name: $ownership})
                CREATE (h:HealthCenter {
                    name: $name,
                    latitude: $lat,
                    longitude: $long,
                    ll_source: $source
                })
                MERGE (h)-[:LOCATED_IN]->(a)
                MERGE (h)-[:OF_TYPE]->(ft)
                MERGE (h)-[:OWNED_BY]->(o)
                MERGE (h)-[:IN_COUNTRY]->(c)
                """,
                {
                    "country": row["Country"],
                    "province": row["Admin1"],
                    "name": row["Facility_n"],
                    "type": row["Facility_t"],
                    "ownership": row["Ownership"],
                    "lat": row["Lat"],
                    "long": row["Long"],
                    "source": row.get("LL_source", "unknown")
                },
            )
    driver.close()

# Function to upload doctors to Neo4j
def upload_doctors_to_neo4j(df_doctors, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        for _, row in df_doctors.iterrows():
            session.run(
                """
                MERGE (d:Doctor {name: $name})
                SET d.description = $description
                MERGE (s:Specialty {name: $specialty})
                MERGE (d)-[:HAS_SPECIALTY]->(s)
                WITH d
                MATCH (h:HealthCenter {name: $hospital})
                MERGE (d)-[:WORKS_AT]->(h)
                """,
                {
                    "name": row["name"],
                    "specialty": row["specialty"],
                    "description": row["description"],
                    "hospital": row["hospital"]
                }
            )
    driver.close()

# Upload button
if st.button("Upload Data to Neo4j"):
    upload_healthcenters_to_neo4j(df_hc, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    upload_doctors_to_neo4j(df_doctors, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    st.success("Local data uploaded to Neo4j!")

# Web search function
def search_web(query, location="RW", city="Kigali"):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={
                "user_location": {
                    "type": "approximate",
                    "approximate": {
                        "country": location,
                        "city": city,
                        "region": city
                    }
                },
                "search_context_size": "medium"
            },
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message
    

    except Exception as e:
        return {"content": f"Web search failed: {e}"}


st.header("Search Rwanda Health Info")

question = st.text_input("Ask about doctors or health centers")

if question:

    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

        schema_prompt = """
You are a Cypher assistant for a Neo4j healthcare graph. Use only this schema:

Nodes:
- Country: name
- Province: name
- Admin1: name
- HealthCenter: name, latitude, longitude, ll_source
- FacilityType: name
- Ownership: name
- Doctor: name, description
- Specialty: name

Relationships:
- (Province)-[:IN_COUNTRY]->(Country)
- (HealthCenter)-[:LOCATED_IN]->(Admin1)
- (HealthCenter)-[:OF_TYPE]->(FacilityType)
- (HealthCenter)-[:OWNED_BY]->(Ownership)
- (HealthCenter)-[:IN_COUNTRY]->(Country)
- (Doctor)-[:HAS_SPECIALTY]->(Specialty)
- (Doctor)-[:WORKS_AT]->(HealthCenter)

Examples:
Q: Show public health centers in East Province
A: MATCH (h:HealthCenter)-[:LOCATED_IN]->(a:Admin1)
WHERE a.name = "East" 
RETURN h.name

Q: Doctors treating elderly in Kigali
A: MATCH (d:Doctor)-[:WORKS_AT]->(h:HealthCenter)-[:LOCATED_IN]->(a:Admin1)
WHERE toLower(d.description) CONTAINS "elderly" AND toLower(a.name) CONTAINS "kigali"
RETURN d.name, d.specialty, h.name AS hospital
"""

        chain = GraphCypherQAChain.from_llm(
            llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,
            cypher_prompt_template=schema_prompt
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

                if hasattr(web_result, "annotations"):
                    for a in web_result.annotations:
                        if a["type"] == "url_citation":
                            url_info = a["url_citation"]
                            st.markdown(f"[Source: {url_info['title']}]({url_info['url']})")
        else:
            st.markdown(f"**Answer:** {graph_answer}")
            st.code(result["intermediate_steps"], language="cypher")

    except Exception as e:
        st.error(f"{e}")
