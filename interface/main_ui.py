import streamlit as st

# Import placeholder functions
from features.diagnosis import get_diagnosis_from_symptoms
from features.pharmacy_locator import find_pharmacies_with_medicine
from features.doctor_search import find_doctors_by_question

from db.neo4j_interface import upload_doctors_to_neo4j, upload_healthcenters_to_neo4j


def run_app():
    st.set_page_config(page_title="HafiCare")
    st.title(" HafiCare Diagnostic Assistant")
    tabs = st.tabs(["Symptom Checker", "Find Doctors", "Pharmacy Locator"])

    # SYMPTOM CHECKER
    with tabs[0]:
        st.header("Describe Your Symptoms")
        symptoms = st.text_area("What symptoms are you experiencing?")
        if st.button("Get Diagnosis"):
            diagnosis = get_diagnosis_from_symptoms(symptoms)
            st.success(diagnosis)

    #  FIND DOCTORS 
    with tabs[1]:
        st.header("Doctor & Health Center Search")

        if st.button("Upload Data to Neo4j"):
            upload_healthcenters_to_neo4j()
            upload_doctors_to_neo4j()
            st.success("Data uploaded to Neo4j successfully!")

        question = st.text_input("Ask a question about doctors or health centers")
        if question:
            result = find_doctors_by_question(question)
            st.success(result)

    #  PHARMACY LOCATOR 
    with tabs[2]:
        st.header("Search for Medicine Near You")
        medicine = st.text_input("Enter the medicine name")
        if st.button("Find Pharmacies"):
            results = find_pharmacies_with_medicine(medicine)
            if results:
                for item in results:
                    st.markdown(f" {item['pharmacy_name']}, {item['location']} — Available: {item['available']}")
            else:
                st.info("No pharmacy information available.")