# 🚗 Automotive Sensor Intelligence Agent

> An agentic AI system that answers natural language questions about OBD-II vehicle sensor data by intelligently routing between a structured database and semantic document search.

**Stack:** LangGraph · Groq (LLaMA 3.3 70B) · Qdrant Cloud · FastAPI · SQLite · Streamlit

---

## What It Does

Ask a question in plain English. The agent decides whether to:

| Question | Tool | Source |
|---|---|---|
| "Which driver was most aggressive?" | 🗄️ Database Query | SQLite via FastAPI |
| "What does the MIL light indicate?" | 📄 Document Search | OBD-II PDFs via Qdrant |
| "Compare Driver 1's RPM with engine wear" | 🔀 Both | Hybrid retrieval |

---

## Architecture
User Question

│

▼

LangGraph Agent

│

▼

Router Node (LLaMA 3.3 70B via Groq)

│

├── api_tool ──► FastAPI ──► SQLite

│                (structured sensor session data)

│

├── rag_tool ──► Qdrant ──► OBD-II PDF chunks

│                (technical manuals, fault codes)

│

└── both ──► Synthesizer Node ──► Final Answer


## Dataset

Real OBD-II sensor data from 3 drivers across 3 vehicles (Volkswagen Jetta, Seat Leon, Nissan Sentra) collected via CAN protocol in Mexico. 555,000 raw sensor readings aggregated into 557 driving sessions.

| Driver | Vehicle | Sessions | Aggressive Events |
|---|---|---|---|
| D001 | Volkswagen Jetta | 175 | 132,328 |
| D002 | Seat Leon | 185 | 148,535 |
| D003 | Nissan Sentra | 197 | 155,739 |

## Evaluation

Evaluated across 20 benchmark questions (10 API, 8 RAG, 2 hybrid):

- **Routing Accuracy: 89%** (16/18 on questions that completed)
- **Avg Latency: 3.2s**

## Setup

```bash
git clone https://github.com/Bhavnish04/automotive-sensor-agent.git
cd automotive-sensor-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Add your API keys to `.env`:
GROQ_API_KEY=your_key

QDRANT_URL=your_qdrant_url

QDRANT_API_KEY=your_qdrant_key




```bash
# Terminal 1 - Start API
uvicorn backend.main:app --reload

# Terminal 2 - Start UI
streamlit run frontend/app.py
```

