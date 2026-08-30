import streamlit as st
from agent import ask_agent

st.set_page_config(
    page_title="Skylark BI Agent",
    page_icon="🛰️",
    layout="centered",
)

# --- Header ---
st.markdown(
    """
    <h1 style='margin-bottom:0;'>🛰️ Skylark Drones — BI Agent</h1>
    <p style='color:gray;margin-top:4px;'>
        I'm your monday.com business intelligence agent. Ask me about pipeline
        health, deal performance, or project status — I'll query the live
        boards, flag any data quality issues I find, and ask if anything's
        unclear.
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

EXAMPLE_QUESTIONS = [
    "How's our pipeline looking for the energy sector this quarter?",
    "Which work orders are overdue or at risk?",
    "Prepare a quick summary for a leadership update.",
]

# --- Sidebar: quick-start examples + reset ---
with st.sidebar:
    st.subheader("Try asking")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    st.divider()
    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Read-only: this agent never writes back to monday.com.")


def handle_question(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Pulling the latest boards from monday.com..."):
            try:
                reply = ask_agent(st.session_state.messages)
            except Exception:
                reply = (
                    "I hit an issue reaching the data source or the model "
                    "just now — this is usually temporary (e.g. a rate limit "
                    "on the free API tier). Please try again in a moment."
                )
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


# --- Render existing history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle a sidebar example click ---
if "pending_question" in st.session_state:
    q = st.session_state.pop("pending_question")
    handle_question(q)

# --- Handle typed input ---
user_input = st.chat_input("Ask about deals, work orders, or request a leadership summary...")
if user_input:
    handle_question(user_input)
