from neo4j import GraphDatabase
import os
from data.load_data import (
    load_hc_data,
    load_doctor_data,
    load_pakistan_doctor_data,
    load_pharmacy_data,
    load_symptom_condition_data,
)

from llm.openai_model import generate_embedding

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "")
    password = os.getenv("NEO4J_PASSWORD", "")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
    except Exception as e:
        raise Exception(f"Failed to connect to Neo4j: {e}")
    return driver


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

#Upload Pakistin 

def upload_pakistan_doctors_to_neo4j():
    df = load_pakistan_doctor_data()
    
    driver = get_neo4j_driver()
    with driver.session() as session:

        session.run("MATCH (d:Doctor) DETACH DELETE d")
        
        for _, row in df.iterrows():
            session.run(
                """
                MERGE (d:Doctor {name: $name})
                SET d.city = $city
                SET d.description = $description
                MERGE (s:Specialty {name: $specialty})
                MERGE (d)-[:HAS_SPECIALTY]->(s)
                """,
                {
                    "name": row["name"],
                    "city": row["city"],
                    "specialty": row["specialty"],
                    "description": row["description"]
                }
            )
    driver.close()



def upload_pharmacies_to_neo4j():
    df = load_pharmacy_data()

    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run("MATCH (p:Pharmacy) DETACH DELETE p")
        for _, row in df.iterrows():
            session.run(
                """
                MERGE (city:City {name: $city})
                CREATE (p:Pharmacy {
                    name: $name,
                    address: $address,
                    phone: $phone,
                    services: $services
                })
                MERGE (p)-[:LOCATED_IN]->(city)
                """,
                {
                    "name": row["name"],
                    "city": row["city"],
                    "address": row["address"],
                    "phone": row["phone"],
                    "services": row["services"],
                },
            )
    driver.close()
    print("Pharmacies uploaded successfully.")


def upload_symptom_conditions_to_neo4j():
    df = load_symptom_condition_data()

    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run("MATCH (c:Condition) DETACH DELETE c")
        for _, row in df.iterrows():
            session.run(
                """
                CREATE (c:Condition {
                    symptom_summary: $symptom_summary,
                    possible_condition: $possible_condition,
                    advice: $advice,
                    urgency: $urgency
                })
                """,
                {
                    "symptom_summary": row["symptom_summary"],
                    "possible_condition": row["possible_condition"],
                    "advice": row["advice"],
                    "urgency": row["urgency"],
                },
            )
    driver.close()
    print("Symptom/condition knowledge base uploaded successfully.")


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


def condition_embeddings():

    driver = get_neo4j_driver()
    with driver.session() as session:

        result = session.run("""
        MATCH (c:Condition)
        RETURN elementId(c) AS id, c.symptom_summary AS symptom_summary
        """)
        records = result.data()

        for record in records:
            node_id = record["id"]
            embedding = generate_embedding(record["symptom_summary"])
            session.run("""
            MATCH (c:Condition) WHERE elementId(c) = $id
            SET c.embedding = $embedding
            """, {"id": node_id, "embedding": embedding})

    driver.close()
    print("Condition embeddings updated successfully.")


def create_vector_index(index_name: str, label: str, property: str = "embedding", dimensions: int = 1536):
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (n:{label})
            ON n.{property}
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: $dimensions,
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """,
            {"dimensions": dimensions},
        )
    driver.close()
    print(f"Vector index '{index_name}' created successfully.")


def create_doctor_vector_index():
    create_vector_index("doctorEmbeddingIndex", "Doctor")


def create_condition_vector_index():
    create_vector_index("conditionEmbeddingIndex", "Condition")


def create_doctor_clinic_id_index():
    driver = get_neo4j_driver()
    with driver.session() as session:
        session.run(
            "CREATE INDEX doctor_clinic_id_idx IF NOT EXISTS FOR (d:Doctor) ON (d.clinic_id)"
        )
    driver.close()
    print("Doctor clinic_id index created successfully.")


def upsert_clinic_doctor(doctor_id: int, clinic_id: int, name: str, specialty: str, bio: str):
    embedding = generate_embedding(f"{name} {specialty} {bio}")

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            session.run(
                """
                MERGE (d:Doctor {postgres_doctor_id: $doctor_id})
                SET d.clinic_id = $clinic_id,
                    d.name = $name,
                    d.description = $bio,
                    d.embedding = $embedding,
                    d.is_active = true
                MERGE (s:Specialty {name: $specialty})
                MERGE (d)-[:HAS_SPECIALTY]->(s)
                """,
                {
                    "doctor_id": doctor_id,
                    "clinic_id": clinic_id,
                    "name": name,
                    "specialty": specialty,
                    "bio": bio,
                    "embedding": embedding,
                },
            )
    finally:
        driver.close()


def deactivate_clinic_doctor(doctor_id: int):
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            session.run(
                "MATCH (d:Doctor {postgres_doctor_id: $doctor_id}) SET d.is_active = false",
                {"doctor_id": doctor_id},
            )
    finally:
        driver.close()
