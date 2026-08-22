import pandas as pd

# Load data
def load_hc_data():
    df_hc = pd.read_csv("data/data/Rwanda_healthcenter.csv")
    
    return df_hc

def load_doctor_data():
    df_doctors = pd.read_csv("data/data/Kigali_Doctors.csv").rename(columns={
        "Name": "name",
        "Specialty": "specialty",
        "Hospital": "hospital",
        "Description": "description"
    })
    
    return df_doctors

def load_data():
    df_hc = load_hc_data()
    df_doctors = load_doctor_data()
    
    return df_hc, df_doctors


def load_pakistan_doctor_data():
    df_pakistan = pd.read_csv("data/data/Pakistan_Doctors.csv")
    df_pakistan.columns = df_pakistan.columns.str.strip()
    df_pakistan = df_pakistan.rename(columns={
        "Name": "name",
        "City": "city",
        "Specialization": "specialty",
        "Hospital": "hospital",
        "description": "description"
    })
    return df_pakistan


def load_pharmacy_data():
    df_pharmacies = pd.read_csv("data/data/Rwanda_Pharmacies.csv")

    return df_pharmacies


def load_symptom_condition_data():
    df_conditions = pd.read_csv("data/data/Symptom_Conditions.csv")

    return df_conditions
