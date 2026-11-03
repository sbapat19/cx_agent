"""Run the API with a tiny stand-in model instead of Gemini, to smoke-test the UI/wiring WITHOUT a key.

    pipenv run python scripts/dev_fake_server.py        (serves on :8000)

The stand-in follows a fixed script for the 'damaged order' scenario only. It is NOT the advisor's real behaviour.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("GOOGLE_API_KEY", "fake-for-wiring-test")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/fake_server.db")

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402

from app import llm  # noqa: E402


class FlowModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages, *a, **k):
        first = messages[0].content if messages else ""
        if "Classify the customer's latest message" in first:
            return AIMessage(content=json.dumps({"intent": "ORDER_ISSUE", "reason": "stand-in router"}))
        last_h = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
        after = messages[last_h + 1:]
        tool_msgs = [m for m in after if isinstance(m, ToolMessage)]
        if not tool_msgs:
            return AIMessage(content="", tool_calls=[{"name": "check_return_eligibility", "args": {"order_id": "ORD-1001", "issue_type": "damaged"}, "id": "c1"}])
        res = json.loads(tool_msgs[-1].content)
        return AIMessage(content=("[stand-in model] I'm sorry about the damaged pump. Order ORD-1001 is inside the return window. "
                                  "The policy doesn't state a replacement for damaged items, so I can either start a standard return or open a support case for human review. "
                                  f"(eligible={res.get('eligible')}, automatic remedy authorized={res.get('automatic_remedy_authorized')}). Which would you like?"))


llm.gemini = lambda model=None: FlowModel()

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("BACKEND_PORT", "8000")))
