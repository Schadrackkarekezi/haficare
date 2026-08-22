from db.neo4j_interface import get_neo4j_driver


def find_pharmacies_by_city(city: str) -> list[dict]:
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            results = session.run(
                """
                MATCH (p:Pharmacy)-[:LOCATED_IN]->(c:City)
                WHERE toLower(c.name) = toLower($city)
                RETURN p.name AS name, p.address AS address, p.phone AS phone, p.services AS services
                ORDER BY p.name
                """,
                {"city": city},
            )
            return [
                {
                    "name": r["name"],
                    "address": r["address"],
                    "phone": r["phone"],
                    "services": r["services"],
                }
                for r in results
            ]
    finally:
        driver.close()
