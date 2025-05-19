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