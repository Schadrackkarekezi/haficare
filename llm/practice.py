from typing import List, Dict, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import asyncio

import streamlit as st

doctor_data = [
    {"name": "Dr. Amina", "city": "Kigali", "specialty": "General"},
    {"name": "Dr. Jean", "city": "Butare", "specialty": "Neurology"},
    {"name": "Dr. Kwizera", "city": "Kigali", "specialty": "Pediatrics"},
    {"name": "Dr. Habimana", "city": "Gisenyi", "specialty": "Cardiology"},
    {"name": "Dr. Uwase", "city": "Huye", "specialty": "Dermatology"},
]


pharmacy_data = [
    {"name": "City Pharmacy", "city": "Kigali"},
    {"name": "Butare Meds", "city": "Butare"},
    {"name": "Huye Health Hub", "city": "Huye"},
    {"name": "Gisenyi Drugs", "city": "Gisenyi"},
]




def get_doctors_by_city(city: str) -> List[Dict]:
    return [doc for doc in doctor_data if doc["city"].lower() == city.lower()]


def get_pharmacies_by_city(city: str) -> List[Dict]:
    return [pharmacy for pharmacy in pharmacy_data if pharmacy["city"].lower() == city.lower()]


class ChatOutput(BaseModel):
    response: str = Field(description="AI response to the user")
    target: Literal['doctor','pharmacy','symptoms','unknown'] = Field(
        default="unknown",
        description="User's goal from the conversations")

agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=ChatOutput,
    system_prompt=(
        "You are a helpful AI medical assistant for patients in Rwanda. "
        " your main job is to figure out what the user wants"
        "you must always include a target field "
        "valid values for the target are 'unknown', 'doctor', 'pharmacy', or 'symptoms''"
        "if you are not sure about the target ask follow up questions until you are sure and please do not assume keep asking until the user's goal is clear "
        "for exmaple If the target is 'doctor', and the user gives a city, automatically use the find_doctor_by_city tool to help them or  if the target is pharmacy then user pharmacy"

    )
)


@agent.tool
def find_doctor_by_city(ctx: RunContext, city: str) -> List[Dict]:
    return get_doctors_by_city(city)


@agent.tool
def find_pharmacy_by_city(ctx: RunContext, city: str) -> List[Dict]:
    return get_pharmacies_by_city(city)



#interface


st.title("HafiCare")

if "message_history" not in st.session_state:
    st.session_state.message_history = []
    st.session_state.last_messages = []

for message in st.session_state.message_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask me anything about doctors or pharmacies in Rwanda")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.message_history.append({"role": "user", "content": user_input})
    
    async def run_agent():
        result = await agent.run(user_input, message_history=st.session_state.last_messages)
        return result

    result = asyncio.run(run_agent())

    st.chat_message("assistant").markdown(result.output.response)
    st.session_state.message_history.append({"role": "assistant", "content": result.output.response})
    st.session_state.last_messages = result.all_messages()






