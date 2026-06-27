from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import ask


st.set_page_config(
    page_title="Automotive Sensor Intelligence Agent",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 Automotive Sensor Intelligence Agent")
st.caption("Ask questions about OBD-II driving data. The agent routes between database and document search automatically.")



with st.sidebar:
    st.markdown("## 🚗 Automotive Agent")
    st.markdown("**Stack:** LangGraph · Gemini 2.5 Flash · FastAPI · SQLite")
    st.divider()

    st.markdown("### 💡 Example Questions")
    examples = [
        "Which driver was most aggressive?",
        "Compare all three drivers",
        "Which vehicle had the highest average RPM?",
        "How many sessions did Driver 2 have?",
        "What does high RPM with aggressive throttle indicate?",
        "Which driver had the highest max speed?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state["pending_question"] = ex

    st.divider()
    st.markdown("### 🔧 Routing Legend")
    st.markdown("🗄️ **Database Query** — structured facts")
    st.markdown("📄 **Document Search** — technical docs")
    st.markdown("🔀 **Both** — hybrid questions")
    
    
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            route = msg.get("route", "")
            if route == "api":
                st.info("🗄️ Agent used: Database Query")
            elif route == "rag":
                st.info("📄 Agent used: Document Search")
            elif route == "both":
                st.info("🔀 Agent used: Both")
            st.caption(f"Reason: {msg.get('routing_reason', '')}")
        st.markdown(msg["content"])

# Handle input
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    user_input = st.chat_input("Ask about driving sensor data...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent thinking..."):
            result = ask(user_input)

            route = result["route"]
            if route == "api":
                st.info("🗄️ Agent used: Database Query")
            elif route == "rag":
                st.info("📄 Agent used: Document Search")
            elif route == "both":
                st.info("🔀 Agent used: Both")

            st.caption(f"Reason: {result['routing_reason']}")
            st.markdown(result["final_answer"])

            st.session_state.messages.append({
                "role":           "assistant",
                "content":        result["final_answer"],
                "route":          route,
                "routing_reason": result["routing_reason"],
            })