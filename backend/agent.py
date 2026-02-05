"""LangGraph supplement-brand refund/resolution router + specialist agents and /chat endpoint."""
import json
import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LLM used for routing and all specialist agents
def _llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)


VALID_CLASSIFICATIONS = {"REFUND", "REPLACEMENT", "STORE_CREDIT", "NEEDS_CLARIFICATION", "OUT_OF_SCOPE"}


class ChatState(TypedDict):
    """State for the refund/resolution router + specialist agent graph."""

    message: str
    classification: str
    clarifying_question: str
    response: str


# --- Router agent: classify into resolution workflow ---
ROUTER_SYSTEM = """You analyze customer support messages for a supplement brand. Classify each message into the correct resolution workflow, or mark it out of scope.

Decision rules:

OUT_OF_SCOPE: The message is clearly unrelated to supplement customer support or refund/return issues (e.g. random chat, unrelated products, nonsense, unrelated services).

REPLACEMENT: The customer reports any of: product arrived damaged or defective; seal broken on arrival; leaking container; missing items; wrong item shipped.

REFUND: The customer wants to return a product that is unopened and unused, with no defect claim.

STORE_CREDIT: The product was opened or used and the customer says it "didn't work," "didn't like it," has taste issues or side effects, without claiming a defect on arrival.

NEEDS_CLARIFICATION: One missing fact would change the outcome (most commonly: opened vs unopened, or defect on arrival vs dissatisfaction after use). Ask exactly one targeted clarifying question that most reduces uncertainty. Do not ask multiple questions. For ambiguous refund or return requests: If the message mentions “refund” or “return” (or similar phrasing) n
and it does NOT clearly state whether the product was opened or used:
→ Route to NEEDS_CLARIFICATION

In this case, ask exactly one clarifying question:
“Have you opened or used the product yet? Either way, I’m happy to help.”


Output format: Return a JSON object only, with no other text. Use this exact structure:
{"classification": "<one of REFUND, REPLACEMENT, STORE_CREDIT, NEEDS_CLARIFICATION, OUT_OF_SCOPE>", "clarifying_question": "<one targeted question string, or null if not NEEDS_CLARIFICATION>", "rationale": "<one sentence explaining your decision>"}"""


def router_node(state: ChatState) -> dict:
    """Classify customer message and optionally set clarifying_question."""
    llm = _llm()
    msg = state["message"].strip()
    response = llm.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=msg),
        ]
    )
    raw = (response.content or "").strip()
    # Extract JSON if wrapped in markdown code block
    json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            classification = (data.get("classification") or "").strip().upper().replace(" ", "_")
            if classification not in VALID_CLASSIFICATIONS:
                classification = "NEEDS_CLARIFICATION"
            clarifying = data.get("clarifying_question")
            clarifying_question = str(clarifying).strip() if clarifying else ""
            return {"classification": classification, "clarifying_question": clarifying_question}
        except (json.JSONDecodeError, TypeError):
            pass
    # Fallback
    return {"classification": "NEEDS_CLARIFICATION", "clarifying_question": ""}


def route_by_classification(state: ChatState) -> str:
    """Return the next node name from classification."""
    return state["classification"].upper().replace(" ", "_")


# --- REFUND agent ---
REFUND_SYSTEM = """You handle cases where the customer qualifies for a refund of an unopened/unused product. Assume refund eligibility has already been approved by the router.

You are a friendly support rep for Bloom Supplements (a modern DTC supplement brand). Be warm, conversational, and on-brand. Your goal is to clearly explain next steps and move toward resolution.

Always ask for both the order number and the email used at checkout. Do not claim the refund has already been issued (demo mode).

Structure your response as follows. Use a new paragraph between the "ask for info" section and the "next steps" section:
(1) Confirm eligibility in a warm, concise way.
(2) Ask for the order number and the email used at checkout.
(3) Start a new paragraph, then explain what happens next: e.g. "We'll process your refund once we have that. You can expect the funds to be returned to your original payment method within 5–7 business days."
Keep the tone warm and conversational, not formal."""


def refund_node(state: ChatState) -> dict:
    """Handle refund-eligible unopened/unused returns."""
    llm = _llm()
    response = llm.invoke(
        [
            SystemMessage(content=REFUND_SYSTEM),
            HumanMessage(content=state["message"]),
        ]
    )
    return {"response": (response.content or "").strip()}


# --- REPLACEMENT agent ---
REPLACEMENT_SYSTEM = """You handle damaged, defective, missing, or incorrect orders and move toward replacement for Bloom Supplements. Assume replacement is the correct resolution. Be warm, conversational, and on-brand for a modern DTC supplement company.

(1) Apologize briefly for the issue.
(2) Ask for the order number, the email used at checkout, and—if relevant—a photo of the damage, broken seal, or incorrect item.
(3) Start a new paragraph.
(4) Explain that once you have that information, the issue will be reviewed and a replacement will be arranged. Do not promise specific shipping timelines (demo mode). Keep the tone concise, professional, and reassuring."""


def replacement_node(state: ChatState) -> dict:
    """Handle damaged/defective/missing/wrong item and arrange replacement."""
    llm = _llm()
    response = llm.invoke(
        [
            SystemMessage(content=REPLACEMENT_SYSTEM),
            HumanMessage(content=state["message"]),
        ]
    )
    return {"response": (response.content or "").strip()}


# --- STORE CREDIT agent ---
STORE_CREDIT_SYSTEM = """You handle cases where the product was opened/used and the customer is dissatisfied. You represent Bloom Supplements. Be warm, conversational, and on-brand for a modern DTC supplement company. Be empathetic but policy-consistent.

(1) Lead with empathy so the customer feels heard.
(2) Explain that opened products qualify for store credit and that they can choose from Bloom's full range of supplements. Recommend NightWish as an example—it has a 4.8★ rating and helps with winding down before bed.
(3) Ask for the order number and the email used at checkout to proceed. Keep the response concise and professional."""


def store_credit_node(state: ChatState) -> dict:
    """Handle opened/used product dissatisfaction with store credit."""
    llm = _llm()
    response = llm.invoke(
        [
            SystemMessage(content=STORE_CREDIT_SYSTEM),
            HumanMessage(content=state["message"]),
        ]
    )
    return {"response": (response.content or "").strip()}


# --- NEEDS CLARIFICATION agent ---
NEEDS_CLARIFICATION_SYSTEM = """You ask one clarifying question to determine the correct resolution path for Bloom Supplements. Be warm and conversational—replace any formal language with a friendlier tone. Example intent: "So glad you asked! Is the bottle unopened?"

Ask one question only. Do not mention internal categories or policy logic. Prefer questions that distinguish opened vs unopened or defect vs dissatisfaction. Reassure the customer that you can help with next steps either way.

If you are given a suggested clarifying question from the system, use it in a warm way and add brief reassurance. Otherwise, generate one clear, friendly question and reassure that you can help either way."""


def needs_clarification_node(state: ChatState) -> dict:
    """Ask one clarifying question and reassure."""
    llm = _llm()
    msg = state["message"]
    suggested = (state.get("clarifying_question") or "").strip()
    if suggested:
        user_content = f"Customer message: {msg}\n\nUse this clarifying question (and add brief reassurance): {suggested}"
    else:
        user_content = msg
    response = llm.invoke(
        [
            SystemMessage(content=NEEDS_CLARIFICATION_SYSTEM),
            HumanMessage(content=user_content),
        ]
    )
    return {"response": (response.content or "").strip()}


# --- OUT OF SCOPE agent (verbatim response, no LLM) ---
OUT_OF_SCOPE_RESPONSE = """This demo shows an agentic workflow for Bloom Supplements that helps customers get a refund or resolution.

To try it out, send a message about a supplement order issue—for example: unopened return, damaged delivery, missing item, or "I tried it and didn't like it."

Thanks for testing!"""


def out_of_scope_node(state: ChatState) -> dict:
    """Return verbatim out-of-scope redirect. No LLM."""
    return {"response": OUT_OF_SCOPE_RESPONSE}


# --- Build the graph ---
graph_builder = StateGraph(ChatState)
graph_builder.add_node("router", router_node)
graph_builder.add_node("REFUND", refund_node)
graph_builder.add_node("REPLACEMENT", replacement_node)
graph_builder.add_node("STORE_CREDIT", store_credit_node)
graph_builder.add_node("NEEDS_CLARIFICATION", needs_clarification_node)
graph_builder.add_node("OUT_OF_SCOPE", out_of_scope_node)

graph_builder.add_edge(START, "router")
graph_builder.add_conditional_edges(
    "router",
    route_by_classification,
    {
        "REFUND": "REFUND",
        "REPLACEMENT": "REPLACEMENT",
        "STORE_CREDIT": "STORE_CREDIT",
        "NEEDS_CLARIFICATION": "NEEDS_CLARIFICATION",
        "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    },
)
graph_builder.add_edge("REFUND", END)
graph_builder.add_edge("REPLACEMENT", END)
graph_builder.add_edge("STORE_CREDIT", END)
graph_builder.add_edge("NEEDS_CLARIFICATION", END)
graph_builder.add_edge("OUT_OF_SCOPE", END)

agent = graph_builder.compile()

# --- FastAPI /chat (unchanged) ---
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    response: str
    route: str
    confidence: float


def _calculate_confidence(route: str) -> float:
    """Calculate deterministic confidence score based on route."""
    if route == "NEEDS_CLARIFICATION":
        return 0.55
    elif route == "OUT_OF_SCOPE":
        return 0.70
    else:
        return 0.80


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Accept a customer support message and return the appropriate agent response."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not set. Add it to .env to use the agent.",
        )
    result = agent.invoke(
        {
            "message": request.message,
            "classification": "",
            "clarifying_question": "",
            "response": "",
        }
    )
    route = result.get("classification", "UNKNOWN")
    confidence = _calculate_confidence(route)
    return ChatResponse(
        response=result["response"],
        route=route,
        confidence=confidence,
    )
