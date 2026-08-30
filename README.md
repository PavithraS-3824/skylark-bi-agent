# Skylark Drones — Monday.com BI Agent

A conversational agent that answers founder-level business questions by
querying live data from two monday.com boards: **Work Orders** (project
execution) and **Deals** (sales pipeline).

## Architecture

- **`monday_client.py`** — Talks to monday.com's GraphQL API directly
  (no MCP server, for setup speed). Fetches all items from a board and
  normalizes messy values: blank/null → `"Unknown"`, inconsistent date
  strings → ISO format, inconsistent casing on text fields. Also collects
  a short list of data-quality notes (missing fields) per fetch.
- **`agent.py`** — Uses Google Gemini's function-calling loop (chosen for
  a free-tier API key with no billing setup required). Gemini is given one
  tool, `_query_monday_board`, and is instructed to always call it fresh
  rather than rely on memory, so answers reflect live board data (never
  hardcoded CSVs). The system prompt asks it to surface data-quality
  caveats and ask clarifying questions when a query is ambiguous.
- **`app.py`** — A minimal Streamlit chat interface wrapping the agent.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in:
   - `MONDAY_API_TOKEN` — from monday.com → profile → Developers → My Access Tokens
   - `GEMINI_API_KEY` — from aistudio.google.com → "Get API key" (free, no card needed)
   - `WORK_ORDERS_BOARD_ID` / `DEALS_BOARD_ID` — the numeric IDs from each
     board's URL (already pre-filled with this project's board IDs)
3. Export the env vars (or use `python-dotenv` / your platform's secrets
   manager) and run:
   ```
   streamlit run app.py
   ```
4. For hosted deployment (e.g. Streamlit Community Cloud): push this repo
   to GitHub, connect it at share.streamlit.io, and add the four variables
   above under the app's "Secrets."

## Notes

- Read-only integration: the agent only reads from monday.com, never writes.
- Data cleaning is intentionally lightweight (date parsing + blank handling)
  given the project timeframe — see the Decision Log for what a production
  version would add.
