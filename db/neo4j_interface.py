


from neo4j import GraphDatabase

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
