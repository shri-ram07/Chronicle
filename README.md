<p align="center">
  <img src="https://img.shields.io/badge/CHRONICLE-Research%20Agent-6366f1?style=for-the-badge&labelColor=1e1b4b" alt="CHRONICLE"/>
</p>

<h1 align="center">CHRONICLE</h1>

<p align="center">
  <strong>From Question to Action: AI Research That Delivers Real Results</strong>
</p>

<p align="center">
  <a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Powered%20by-Gemini%203%20Flash-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/></a>
  <a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Google%20Search-Grounding-34A853?style=flat-square&logo=google&logoColor=white" alt="Grounding"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Gemini%20API-Developer%20Competition-FF6B6B?style=for-the-badge" alt="Hackathon"/>
</p>

<p align="center">
  <a href="https://chronicle-1-mx90.onrender.com">Live Demo</a> •
  <a href="https://github.com/shri-ram07/Chronicle.git">GitHub</a>
</p>

---

## Gemini 3 Integration

CHRONICLE leverages **Gemini 3 Flash** as its core AI engine to power an autonomous 8-phase deep research pipeline:

| Gemini 3 Feature | How We Use It |
|------------------|---------------|
| **Google Search Grounding** | Every query uses real-time web data for current pricing, reviews, and information |
| **Multi-Phase Reasoning** | Powers all 8 phases: Planning, Discovery, Deep Dive, Comparison, Validation, Scoring, Self-Correction, Synthesis |
| **Semantic Quality Scoring** | AI evaluates research depth: "Are these actual prices or just 'contact sales'?" |
| **Structured Output** | Generates JSON with 15+ attributes per entity |
| **75+ API Calls/Mission** | Deep research requires sustained AI reasoning, not single-shot answers |

---

## The Problem

We've all been there: spending **hours** researching competitors, market trends, or potential partners—only to end up with scattered browser tabs and half-finished notes.

> Ask ChatGPT "What are the best project management tools?" and you get a list of names.
>
> But what about actual pricing? Feature comparisons? Pros and cons from real users?

**AI can answer questions. But it can't complete research missions. Until now.**

---

## The Solution

CHRONICLE transforms a single research goal into comprehensive, exportable deliverables.

```
Input:  "Find the best project management tools for remote teams under $20/user"

Output: 15 deeply-researched tools with pricing, features, pros/cons,
        use cases — exported as CSV, JSON, Markdown, and PDF
```

### What Makes It Different

| Metric | ChatGPT | Traditional Research | CHRONICLE |
|--------|---------|---------------------|-----------|
| **Time** | 30 seconds | 4+ hours | 15-30 minutes |
| **Depth** | Surface-level | Varies | 15+ attributes/entity |
| **Queries** | 1 | Manual | 75+ automated |
| **Exports** | Copy/paste | Manual | CSV, JSON, PDF, MD |
| **Quality Control** | None | Manual | Auto self-correction |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHRONICLE ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│  │   FRONTEND   │         │   BACKEND    │         │  GEMINI 3    │    │
│  │  React+SSE   │◄───────►│   FastAPI    │◄───────►│    FLASH     │    │
│  └──────────────┘         └──────────────┘         └──────────────┘    │
│         │                        │                        │             │
│         ▼                        ▼                        ▼             │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│  │ • Progress   │         │ • Mission    │         │ • Search     │    │
│  │   Monitor    │         │   Manager    │         │   Grounding  │    │
│  │ • Findings   │         │ • Event Bus  │         │ • Structured │    │
│  │   Table      │         │ • Exporter   │         │   Output     │    │
│  │ • Exports    │         │ • Persistence│         │ • Reasoning  │    │
│  └──────────────┘         └──────────────┘         └──────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The 8-Phase Deep Research Pipeline

This is CHRONICLE's core innovation. Instead of **1 query = 200 shallow names**, we execute **75+ targeted queries = 15 deeply-researched entities**.

```
[PLAN]──►[DISCOVER]──►[DEEP DIVE]──►[COMPARE]──►[VALIDATE]
                           │                         │
                           │         ┌───────────────┘
                           ▼         ▼
                       [SCORE]◄──[SELF-CORRECT]──►[SYNTHESIZE]
```

### The Deep Dive Innovation

For **each entity**, we run **5 targeted queries**:

```
                    Single Entity (e.g., Notion)
                              │
          ┌───────────┬───────┴───────┬───────────┐
          ▼           ▼               ▼           ▼
      Pricing     Features        Reviews    Competitors
       Query        Query          Query        Query
          │           │               │           │
          ▼           ▼               ▼           ▼
      $10/mo      Databases      Pros/Cons    vs Coda
      $18/mo      Wiki, AI       from users   vs Clickup
```

**Result:** `15 entities × 5 queries = 75+ targeted searches with Google Search Grounding`

---

## Self-Correction Engine

CHRONICLE doesn't just research—it **validates quality** and **re-researches gaps**.

```
Findings ──► Semantic Scoring ──► Depth >= 0.7? ──► YES ──► Done
                                       │
                                       NO
                                       │
                                       ▼
                              Identify Shallow Items
                                       │
                                       ▼
                              Run Targeted Queries
                                       │
                                       ▼
                              Merge & Re-Score
```

**Quality Checks:**
- Are prices actual numbers (not "contact sales")?
- Are features specific (not generic marketing speak)?
- Are there real pros AND cons?
- Are sources cited?

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API Key ([Get free key](https://aistudio.google.com/apikey))

### Backend
```bash
cd chronicle
pip install -r requirements.txt
python run.py
```

### Frontend
```bash
cd chronicle/frontend
npm install
npm run dev
```

### Use It
1. Open http://localhost:3000
2. Paste your Gemini API key
3. Enter a research goal
4. Watch the magic happen

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/research` | Start new mission |
| `GET` | `/api/status/{id}` | Current status |
| `GET` | `/api/status/{id}/stream` | SSE real-time events |
| `GET` | `/api/findings/{id}` | All findings |
| `POST` | `/api/export/{id}` | Export to file |

### Example Request
```bash
curl -X POST https://chronicle-obxb.onrender.com/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Find the top 10 project management tools for startups",
    "api_key": "YOUR_GEMINI_API_KEY"
  }'
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **AI Engine** | Gemini 3 Flash + Google Search Grounding |
| **Backend** | Python, FastAPI, Pydantic v2, Uvicorn |
| **Frontend** | React 18, Tailwind CSS, Vite |
| **Real-time** | Server-Sent Events (SSE) |
| **Export** | ReportLab (PDF), Native CSV/JSON/Markdown |

---

## Project Structure

```
chronicle/
├── app/main.py              # FastAPI application
├── services/
│   └── mission_manager.py   # 8-phase research pipeline
├── routes/
│   ├── research.py          # POST /research
│   ├── status.py            # SSE streaming
│   └── export.py            # File exports
├── models/
│   ├── domain.py            # Mission, DeepFinding
│   └── requests.py          # API models
├── tools/
│   └── file_export.py       # CSV, JSON, MD, PDF
├── frontend/
│   └── src/
│       ├── App.jsx          # Main application
│       └── components/      # UI components
└── exports/                 # Generated files
```

---

## Impact

| Problem | Solution |
|---------|----------|
| 4+ hours of manual research | 15-30 minutes automated |
| Scattered browser tabs | Organized findings table |
| Surface-level lists | 15+ attributes per entity |
| No quality control | Automatic self-correction |
| Copy/paste exports | Professional PDF, CSV, JSON |

**Market:** Research is universal—entrepreneurs, analysts, students, investors, consultants all need deep research capabilities.

---

## Built With

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/Gemini%203-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
</p>

---

## License

MIT License - Built for the Gemini API Developer Competition

---

<p align="center">
  <strong>CHRONICLE: Research That Works While You Don't Have To</strong>
</p>

<p align="center">
  <sub>Powered by Gemini 3 Flash + Google Search Grounding</sub>
</p>
