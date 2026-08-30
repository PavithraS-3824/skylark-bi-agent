"""
Minimal monday.com GraphQL client.
Fetches items from a board and cleans them into a simple list-of-dicts
that's easy for an LLM to reason about.
"""

import os
import requests
from dateutil import parser as dateparser

MONDAY_API_URL = "https://api.monday.com/v2"

BOARD_IDS = {
    "work_orders": os.environ.get("WORK_ORDERS_BOARD_ID", "5030964497"),
    "deals": os.environ.get("DEALS_BOARD_ID", "5030964573"),
}


def _headers():
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        raise RuntimeError("MONDAY_API_TOKEN environment variable is not set.")
    return {"Authorization": token, "Content-Type": "application/json"}


def _clean_value(text):
    """Normalize a raw column text value: fix blanks, try to parse dates."""
    if text is None or text.strip() == "":
        return "Unknown"

    text = text.strip()

    # Try to normalize date-looking strings to ISO format.
    try:
        parsed = dateparser.parse(text, fuzzy=False)
        # Only treat as a date if it round-trips sensibly (avoid mangling
        # plain numbers or short codes that dateutil can over-eagerly parse).
        if len(text) >= 6 and any(ch.isdigit() for ch in text):
            return parsed.date().isoformat()
    except (ValueError, OverflowError):
        pass

    return text.title() if text.isupper() or text.islower() else text


def get_board_items(board_key: str):
    """
    Fetch all items from a monday.com board.
    board_key: "work_orders" or "deals"
    Returns: list of dicts, one per item, with cleaned column values.
    """
    if board_key not in BOARD_IDS:
        raise ValueError(f"Unknown board_key '{board_key}'. Use 'work_orders' or 'deals'.")

    board_id = BOARD_IDS[board_key]

    query = """
    query ($boardId: [ID!]) {
      boards(ids: $boardId) {
        name
        items_page(limit: 500) {
          items {
            name
            column_values {
              id
              column {
                title
              }
              text
            }
          }
        }
      }
    }
    """

    response = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": {"boardId": [board_id]}},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"monday.com API error: {data['errors']}")

    boards = data.get("data", {}).get("boards", [])
    if not boards:
        return []

    items = boards[0]["items_page"]["items"]

    cleaned = []
    quality_notes = []
    for item in items:
        row = {"item_name": item["name"]}
        for cv in item["column_values"]:
            col_title = cv["column"]["title"]
            raw_text = cv["text"]
            if raw_text is None or raw_text.strip() == "":
                quality_notes.append(f"{item['name']} is missing '{col_title}'")
            row[col_title] = _clean_value(raw_text)
        cleaned.append(row)

    return {"items": cleaned, "data_quality_notes": quality_notes[:20]}  # cap notes


if __name__ == "__main__":
    # Quick manual test
    import json
    print(json.dumps(get_board_items("work_orders"), indent=2)[:2000])
