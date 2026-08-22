from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage

from api.chat.schemas import ChatRequest, ChatResponse
from api.deps import AuthenticatedUser, get_current_user
from graph.build import build_graph

router = APIRouter(tags=["chat"])

_GRAPH = None


def _get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: AuthenticatedUser = Depends(get_current_user)):
    graph = _get_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=req.message)],
            "clinic_id": user.clinic_id,
            "patient_user_id": user.user_id if user.role == "patient" else None,
        },
        config={"configurable": {"thread_id": f"{user.user_id}:{req.thread_id}"}},
    )
    return ChatResponse(
        reply=result["result"],
        intent=result.get("intent", "unknown"),
        doctor_recommendations=result.get("doctor_recommendations"),
    )
