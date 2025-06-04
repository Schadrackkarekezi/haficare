from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
import os
from data.load_data import load_hc_data, load_doctor_data

from llm.openai_model import generate_embedding  

def get_neo4j_driver():
    # Get connection data from environment variables
    # Default to empty string to avoid typing warnings in neo4j connection
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
    except Exception as e:
        raise Exception(f"Failed to connect to Neo4j: {e}")
    return driver


def get_neo4j_graph():
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    
    try:
        graph = Neo4jGraph(url=uri, username=user, password=password)
    except Exception as e:
        raise Exception(f"Failed to connect to Neo4j: {e}")
    return graph


def upload_healthcenters_to_neo4j():
    df = load_hc_data()
    
    driver = get_neo4j_driver()
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


def upload_doctors_to_neo4j():
    df = load_doctor_data()
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        for _, row in df.iterrows():
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


# Embedding functions

def doctor_embeddings():

    driver = get_neo4j_driver()
    with driver.session() as session:
        
        result = session.run("""
        MATCH (d:Doctor)
        RETURN d.name AS name, d.description AS description
        """)
        records = result.data()

        for record in records:
            name = record["name"]
            description = record["description"]
            embedding = generate_embedding(description)
            session.run("""
            MATCH (d:Doctor {name: $name})
            SET d.embedding = $embedding
            """, {"name": name, "embedding": embedding})

    driver.close()
    print("Doctor embeddings updated successfully.")




def create_doctor_vector_index():
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run("""
        CREATE VECTOR INDEX doctorEmbeddingIndex IF NOT EXISTS
        FOR (d:Doctor)
        ON d.embedding
        OPTIONS {
          indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
          }
        }
        """)
    driver.close()
    print("Doctor vector index created successfully.")
