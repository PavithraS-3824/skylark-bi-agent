"""
The BI agent: a Gemini function-calling loop.
Gemini decides when it needs data from monday.com, calls the tool,
we execute it against the real boards, and feed results back until
Gemini produces a final natural-language answer.

(Using Google Gemini instead of Claude because Gemini API keys are free
to create at aistudio.google.com with no billing/card required.)
"""

import os
import google.generativeai as genai
from monday_client import get_board_items

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

SYSTEM_PROMPT = """You are a business intelligence assistant for Skylark Drones' \
leadership team. You answer founder-level questions about the company's sales \
pipeline (Deals board) and project execution (Work Orders board).

Rules:
- ALWAYS fetch fresh data via the query_monday_board tool before answering \
  anything about deals or work orders. Never invent numbers or rely on memory \
  of previous calls in this conversation if the question could have new data.
- The data is real-world messy: expect missing fields, inconsistent date \
  formats, and inconsistent naming. Note any relevant data quality issues \
  briefly in your answer (e.g. "3 deals had no close date, excluded from this figure").
- If a question is ambiguous (e.g. unclear time period, unclear sector), \
  ask a brief clarifying question OR state the assumption you're making and proceed.
- Give the founder a clear, direct answer first, then context/insight, not \
  just raw numbers.
- When asked to "prepare something for leadership" or similar, produce a \
  short structured summary (key metrics + notable risks/highlights) rather \
  than a data dump.
"""


def _query_monday_board(board_key: str):
    """Fetch current items from a monday.com board.
    Use 'work_orders' for project execution data, or 'deals' for sales
    pipeline data. Always call this before answering a question about
    either board — never use stale/remembered data.
    """
    try:
        return get_board_items(board_key)
    except Exception as e:
        return {"error": str(e)}


def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=[_query_monday_board],
    )


def ask_agent(conversation_history):
    """
    conversation_history: list of {"role": "user"/"assistant", "content": str}
    Returns: the assistant's final text reply (str).
    """
    model = _get_model()

    # Gemini uses "model" instead of "assistant" as the role name.
    history = []
    for m in conversation_history[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [m["content"]]})

    chat = model.start_chat(history=history, enable_automatic_function_calling=True)
    latest_user_message = conversation_history[-1]["content"]

    response = chat.send_message(latest_user_message)
    return response.text.strip()
