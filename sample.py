from db.neo4j_interface import doctor_embeddings, create_doctor_vector_index
from llm.openai_model import generate_embedding

#if __name__ == "__main__":
    #query_embedding = generate_embedding("doctors in Kigali City")
    #print(query_embedding)

   


import streamlit as st
from db.neo4j_interface import get_neo4j_driver, upload_doctors_to_neo4j, upload_pakistan_doctors_to_neo4j
from llm.openai_model import generate_embedding

st.set_page_config(page_title="HafiCare")

st.title("Doctor Semantic Search")


dataset_choice = st.selectbox(
    "Select the dataset to test:",
    ["Kigali Doctors", "Pakistan Doctors"]
)

if st.button("Load Dataset"):
    st.info(f"Loading {dataset_choice} dataset into Neo4j...")
    if dataset_choice == "Kigali Doctors":
        upload_doctors_to_neo4j()
    else:
        upload_pakistan_doctors_to_neo4j()
    
    
    doctor_embeddings()
    create_doctor_vector_index()
    
    st.success("Dataset loaded and embeddings updated!")


def vector_search_doctors(query: str, top_r: int = 5):
    vec = generate_embedding(query)
    driver = get_neo4j_driver()
    with driver.session() as session:
        results = session.run(
            """
            WITH $vec AS q
            CALL db.index.vector.queryNodes(
              "doctorEmbeddingIndex",
              $k,
              q
            )
            YIELD node, score
            RETURN
              node.name AS name,
              node.specialty AS specialty,
              node.location AS location,
              score
            ORDER BY score DESC
            """,
            {"vec": vec, "k": top_r}
        )
        doctors = [
            {
                "name": r["name"],
                "specialty": r["specialty"],
                "score": r["score"],
            }
            for r in results
        ]
    driver.close()
    return doctors

st.title("Vector Search")

query = st.text_input("Enter symptoms or keywords:")


if st.button("Search"):
    if not query:
        st.warning("Please enter a query.")
    else:
        matches = vector_search_doctors(query)
        if not matches:
            st.error("No doctors found")
        else:
            for i, doc in enumerate(matches, 1):
                st.write(
                    f"**{i}. {doc['name']}** \n"
                    f"Score: {doc['score']:.2f}"
                )


