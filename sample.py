#from db.neo4j_interface import doctor_embeddings, create_doctor_vector_index
from llm.openai_model import generate_embedding

if __name__ == "__main__":


    query_embedding = generate_embedding("doctors in Kigali City")

    print(query_embedding)
    #doctor_embeddings()
    #create_doctor_vector_index()
   
