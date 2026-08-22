import asyncio
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

from graph.build import build_graph


@st.cache_resource
def get_graph():
    return build_graph()


st.title("HafiCare")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.display_history = []

for message in st.session_state.display_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask me about doctors, pharmacies, symptoms, or booking an appointment in Rwanda")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.display_history.append({"role": "user", "content": user_input})

    graph = get_graph()
    result = asyncio.run(
        graph.ainvoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"configurable": {"thread_id": st.session_state.thread_id}},
        )
    )

    response_text = result["result"]
    st.chat_message("assistant").markdown(response_text)
    st.session_state.display_history.append({"role": "assistant", "content": response_text})
