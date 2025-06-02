import streamlit as st
import asyncio
from typing import List, Dict, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from features.doctor_search import find_doctors_by_question 


pharmacy_data = [
    {"name": "City Pharmacy", "city": "Kigali"},
    {"name": "Butare Meds", "city": "Butare"},
    {"name": "Huye Health Hub", "city": "Huye"},
    {"name": "Gisenyi Drugs", "city": "Gisenyi"},
]

def get_pharmacies_by_city(city: str) -> List[Dict]:
    return [pharmacy for pharmacy in pharmacy_data if pharmacy["city"].lower() == city.lower()]


class ChatOutput(BaseModel):
    response: str = Field(description="AI response to the user")
    target: Literal['doctor', 'pharmacy', 'symptoms', 'unknown'] = Field(
        default="unknown",
        description="User's goal from the conversation"
    )

agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=ChatOutput,
    system_prompt=(
        "You are a helpful AI medical assistant for patients in Rwanda. "
        "Your main job is to figure out what the user wants. "
        "You must always include a target field: valid values are 'unknown', 'doctor', 'pharmacy', or 'symptoms'. "
        "If you are not sure about the target, ask follow-up questions until you are sure. "
        "Please do not assume; keep asking until the user's goal is clear. "
        "If the user's target is 'doctor call the 'answer_health_question'"
        "If the target is 'pharmacy', call the 'find_pharmacy_by_city' tool."
    )
)

#Answer question realated to doctor
@agent.tool
def answer_health_question(ctx: RunContext, question: str) -> str:
    return find_doctors_by_question(question)

#City-based doctor search
#@agent.tool
#def find_doctor_by_city(ctx: RunContext, city: str) -> List[Dict]:
    #return get_doctors_by_city(city)



@agent.tool
def find_pharmacy_by_city(ctx: RunContext, city: str) -> List[Dict]:
    return get_pharmacies_by_city(city)

# Streamlit UI

st.title("HafiCare")

if "message_history" not in st.session_state:
    st.session_state.message_history = []
    st.session_state.last_messages = []

for message in st.session_state.message_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask me anything about doctors or health centers in Rwanda")

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


    st.markdown(f"**Target:** {result.output.target}")
