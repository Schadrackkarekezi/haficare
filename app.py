

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
    question: str = Field(
        default="",
        description="The user's medical query, to be passed into the doctor search tool"
    )



agent = Agent(
    model="openai:gpt-4o-mini",
    output_type=ChatOutput,
    system_prompt=(
        "You are a helpful AI medical assistant for patients in Rwanda. "
        "Your job is to figure out what the user wants. Valid targets are: 'doctor', 'pharmacy', 'symptoms', or 'unknown'. "
        "Always include the 'target' field. "
        "If the target is 'doctor', include the user's question in the 'question' field and call the 'answer_health_question' tool immediately. "
        "If the target is 'pharmacy', include 'city' and call the 'find_pharmacy_by_city' tool. "
        "Only reply directly if no tool applies. If you're unsure of the user's intent, ask follow-up questions until you're certain."
    )
)


#Doctor search tool

@agent.tool
def answer_health_question(ctx: RunContext, question: str) -> str:
    return find_doctors_by_question(question)


#Pharmacy tool
@agent.tool
def find_pharmacy_by_city(ctx: RunContext, city: str) -> List[Dict]:
    return get_pharmacies_by_city(city)


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

    st.markdown(f"**Target:** `{result.output.target}`")
    if result.output.target == "doctor":
        st.markdown(f"**Doctor Search Input:** `{result.output.question}`")
