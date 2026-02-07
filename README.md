<p align="center">
  <img src="https://img.shields.io/badge/CHRONICLE-Research%20Agent-6366f1?style=for-the-badge&labelColor=1e1b4b" alt="CHRONICLE"/>
</p>

<h1 align="center">CHRONICLE</h1>

<p align="center">
  <strong>From Question to Action: AI Research That Delivers Real Results</strong>
</p>

<p align="center">
  <a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Powered%20by-Gemini%202.0%20Flash-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/></a>
  <a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Google%20Search-Grounding-34A853?style=flat-square&logo=google&logoColor=white" alt="Grounding"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Gemini%20API-Developer%20Competition-FF6B6B?style=for-the-badge" alt="Hackathon"/>
</p>

---

## The Problem

We've all been there: spending **hours** researching competitors, market trends, or potential partners—only to end up with a messy collection of browser tabs and half-finished notes.

Current AI assistants can *answer* questions, but they can't *complete* research missions.

> Ask ChatGPT "What are the best project management tools?" and you get a list of names.
>
> But what about actual pricing? Feature comparisons? Pros and cons from real users?

**CHRONICLE changes everything.**

---

## The Solution

CHRONICLE is a **Marathon Research-to-Action Agent** that transforms a single goal into comprehensive, exportable deliverables.

```
Input:  "Find the best project management tools for remote teams under $20/user"

Output: 15 deeply-researched tools with pricing, features, pros/cons,
        use cases — exported as CSV, JSON, Markdown, and PDF
```

While you grab coffee (or sleep), CHRONICLE autonomously:

| Phase | What Happens |
|-------|--------------|
| **Discovery** | Finds 20-50 candidates from multiple search angles |
| **Deep Dive** | Researches EACH entity with 5+ targeted queries |
| **Comparison** | Head-to-head entity comparisons |
| **Validation** | Verifies claims with additional sources |
| **Self-Correction** | Re-researches shallow findings automatically |
| **Export** | Generates CSV, JSON, Markdown, and PDF reports |

---

## Architecture

```mermaid
flowchart TB
    subgraph Frontend[Frontend - React + Tailwind]
        UI[User Interface]
        SSE[Real-time SSE Client]
        DL[Export Downloads]
    end

    subgraph Backend[Backend - FastAPI]
        API[REST API]
        MM[Mission Manager]
        EB[Event Bus]
        EX[File Exporter]
    end

    subgraph AI[AI Engine - Gemini 2.0 Flash]
        LLM[Gemini LLM]
        GS[Google Search Grounding]
    end

    subgraph Storage[Persistence]
        MS[Mission Store]
        FS[File System]
    end

    UI -->|POST /research| API
    API -->|Create & Run| MM
    MM -->|Query with Search| LLM
    LLM -->|Ground Results| GS
    MM -->|Emit Events| EB
    EB -->|Stream Updates| SSE
    MM -->|Save State| MS
    MM -->|Generate Files| EX
    EX -->|Write| FS
    FS -->|Download| DL

    style Frontend fill:#3b82f6,color:#fff
    style Backend fill:#10b981,color:#fff
    style AI fill:#8b5cf6,color:#fff
    style Storage fill:#6b7280,color:#fff
```

---

## The 8-Phase Deep Research Pipeline

This is CHRONICLE's core innovation. Instead of **1 query = 200 shallow names**, we execute **75+ targeted queries = 15 deeply-researched entities**.

```mermaid
flowchart LR
    P1[Planning] --> P2[Discovery]
    P2 --> P3[Deep Dive]
    P3 --> P4[Comparison]
    P4 --> P5[Validation]
    P5 --> P6[Scoring]
    P6 --> P7[Self-Correction]
    P7 --> P8[Synthesis]

    style P1 fill:#3b82f6,color:#fff
    style P2 fill:#6366f1,color:#fff
    style P3 fill:#8b5cf6,color:#fff
    style P4 fill:#a855f7,color:#fff
    style P5 fill:#d946ef,color:#fff
    style P6 fill:#ec4899,color:#fff
    style P7 fill:#f97316,color:#fff
    style P8 fill:#22c55e,color:#fff
```

### The Deep Dive Innovation

For **each entity**, we run **5 targeted queries**:

```mermaid
flowchart TB
    Entity[Single Entity: Notion]

    subgraph Queries[5 Targeted Queries per Entity]
        Q1[Pricing Query]
        Q2[Features Query]
        Q3[Reviews Query]
        Q4[Competitors Query]
        Q5[Use Cases Query]
    end

    subgraph Output[Rich Data Extracted]
        O1[Pricing tiers and costs]
        O2[Detailed feature list]
        O3[Pros and cons]
        O4[Competitor comparison]
        O5[Target audience]
    end

    Entity --> Q1 & Q2 & Q3 & Q4 & Q5
    Q1 --> O1
    Q2 --> O2
    Q3 --> O3
    Q4 --> O4
    Q5 --> O5

    O1 & O2 & O3 & O4 & O5 --> Result[DeepFinding with 15+ Attributes]

    style Entity fill:#1e40af,color:#fff
    style Result fill:#15803d,color:#fff
```

**Result:** `15 entities × 5 queries = 75+ targeted searches`

---

## Self-Correction Engine

CHRONICLE doesn't just research—it **validates quality** and **re-researches gaps**.

```mermaid
flowchart TB
    Findings[All Findings] --> Score[Semantic Quality Scoring]

    Score --> Check{Depth Score >= 0.7?}

    Check -->|Yes| Done[Move to Synthesis]
    Check -->|No| Identify[Identify Shallow Findings]

    Identify --> Reresearch[Run Targeted Queries]
    Reresearch --> Merge[Merge New Data]
    Merge --> Score

    style Done fill:#22c55e,color:#fff
    style Identify fill:#f97316,color:#fff
    style Reresearch fill:#ef4444,color:#fff
```

**Quality checks:**
- Are prices actual numbers (not "contact sales")?
- Does it have 5+ specific features?
- Are there real pros AND cons?
- Are sources cited?

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- Gemini API Key ([Get free key](https://aistudio.google.com/apikey))

### 1. Backend Setup

```bash
cd chronicle
pip install -r requirements.txt
python run.py
```

Server runs at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd chronicle/frontend
npm install
npm run dev
```

Dashboard at `http://localhost:3000`

### 3. Start Researching

1. Open `http://localhost:3000`
2. Paste your Gemini API key
3. Enter a research goal
4. Watch the magic happen in real-time

---

## API Reference

```mermaid
flowchart LR
    subgraph Research[Research]
        R1[POST /api/research]
        R2[GET /api/research/:id]
        R3[DELETE /api/research/:id]
    end

    subgraph Status[Real-time Status]
        S1[GET /api/status/:id]
        S2[GET /api/status/:id/stream]
    end

    subgraph Export[Export]
        E1[POST /api/export/:id]
        E2[GET /api/findings/:id]
    end

    style Research fill:#3b82f6,color:#fff
    style Status fill:#8b5cf6,color:#fff
    style Export fill:#22c55e,color:#fff
```

### Start a Research Mission

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Find the top 10 project management tools for startups",
    "api_key": "YOUR_GEMINI_API_KEY",
    "criteria": {
      "required_fields": ["name", "description", "pricing", "features"],
      "quality_threshold": 0.7,
      "max_results": 15
    },
    "actions": {
      "export_formats": ["json", "csv", "pdf", "md"]
    }
  }'
```

### Response

```json
{
  "mission_id": "chr_abc123",
  "status": "planning",
  "stream_url": "/api/status/chr_abc123/stream",
  "message": "Mission started successfully"
}
```

---

## Tech Stack

```mermaid
flowchart TB
    subgraph Frontend[Frontend]
        React[React 18]
        Tailwind[Tailwind CSS]
        Vite[Vite]
    end

    subgraph Backend[Backend]
        FastAPI[FastAPI]
        Pydantic[Pydantic v2]
        SSE[SSE-Starlette]
    end

    subgraph AI[AI Layer]
        Gemini[Gemini 2.0 Flash]
        Search[Google Search Grounding]
    end

    subgraph Export[Export Engine]
        PDF[ReportLab PDF]
        CSV[Native CSV]
        JSON[Native JSON]
    end

    Frontend --> Backend
    Backend --> AI
    Backend --> Export

    style Frontend fill:#61dafb,color:#000
    style Backend fill:#009688,color:#fff
    style AI fill:#4285f4,color:#fff
    style Export fill:#ef4444,color:#fff
```

| Layer | Technology |
|-------|------------|
| **AI Engine** | Gemini 2.0 Flash + Google Search Grounding |
| **Backend** | FastAPI, Pydantic v2, Uvicorn |
| **Frontend** | React 18, Tailwind CSS, Vite |
| **Real-time** | Server-Sent Events (SSE) |
| **Export** | ReportLab (PDF), Native CSV/JSON/Markdown |

---

## Project Structure

```
chronicle/
├── app/                    # FastAPI application entry
│   └── main.py            # CORS, routes, middleware
├── services/
│   └── mission_manager.py # 8-phase research pipeline
├── routes/
│   ├── research.py        # POST /research, GET /research/:id
│   ├── status.py          # SSE streaming, status polling
│   └── export.py          # File export endpoints
├── models/
│   ├── domain.py          # Mission, DeepFinding, ResearchPlan
│   └── requests.py        # API request/response models
├── tools/
│   └── file_export.py     # CSV, JSON, MD, PDF generation
├── persistence/
│   └── mission_store.py   # In-memory + file persistence
├── config/
│   └── settings.py        # Pydantic settings
├── frontend/              # React dashboard
│   └── src/
│       ├── App.jsx        # Main application
│       └── components/    # UI components
└── exports/               # Generated report files
```

---

## What Makes CHRONICLE Different

```mermaid
flowchart LR
    subgraph Before[Traditional Research]
        T1[1 Query] --> T2[200 Names]
        T2 --> T3[No Details]
    end

    subgraph After[CHRONICLE Research]
        C1[75+ Queries] --> C2[15 Entities]
        C2 --> C3[15+ Attributes Each]
    end

    Before -.->|CHRONICLE| After

    style Before fill:#dc2626,color:#fff
    style After fill:#16a34a,color:#fff
```

| Metric | ChatGPT | Traditional Research | CHRONICLE |
|--------|---------|---------------------|-----------|
| **Time** | 30 seconds | 4+ hours | 15-30 minutes |
| **Depth** | Surface-level list | Varies | 15+ attributes per entity |
| **Queries** | 1 | Manual | 75+ automated |
| **Exports** | Copy/paste | Manual formatting | CSV, JSON, PDF, Markdown |
| **Quality Control** | None | Manual review | Automated self-correction |

---

## Demo Scenarios

### Startup Research
```
Goal: "Find 10 AI startups in healthcare that raised Series A-B in 2024"

Output:
├── 10 startups with funding details, investors, descriptions
├── Comparison matrix of all startups
├── Executive summary with key insights
└── Exports: startup_research.csv, report.pdf
```

### Competitive Intelligence
```
Goal: "Research top 5 competitors in project management software"

Output:
├── Feature comparison across all competitors
├── Pricing analysis with tier breakdowns
├── Pros/cons from user reviews
└── Exports: competitive_analysis.pdf, data.json
```

### Market Analysis
```
Goal: "Identify emerging trends in sustainable packaging"

Output:
├── Key players and market leaders
├── Technology trends and innovations
├── Regulatory landscape analysis
└── Exports: market_report.pdf, findings.csv
```

---

## Export Formats

```mermaid
flowchart LR
    Mission[Research Complete] --> JSON[JSON - Full Data]
    Mission --> CSV[CSV - Spreadsheet]
    Mission --> MD[Markdown - Report]
    Mission --> PDF[PDF - Professional]

    style JSON fill:#f59e0b,color:#000
    style CSV fill:#10b981,color:#fff
    style MD fill:#3b82f6,color:#fff
    style PDF fill:#ef4444,color:#fff
```

| Format | Best For |
|--------|----------|
| **JSON** | Developers, integrations, further processing |
| **CSV** | Excel/Sheets analysis, data manipulation |
| **Markdown** | Documentation, GitHub, note-taking apps |
| **PDF** | Stakeholder reports, professional sharing |

---

## Roadmap

- [x] 8-phase deep research pipeline
- [x] Real-time SSE streaming
- [x] Self-correction engine
- [x] Multi-format export (JSON, CSV, MD, PDF)
- [x] User-provided API keys
- [ ] Pause/Resume with checkpoints
- [ ] Email notifications
- [ ] Webhook integrations
- [ ] Collaborative research sessions
- [ ] Custom export templates

---

## Built With

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Tailwind-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
</p>

---

## License

MIT License - Built for the Gemini API Developer Competition

---

<p align="center">
  <strong>CHRONICLE: Research That Works While You Don't Have To</strong>
</p>

<p align="center">
  <sub>Built with Gemini 2.0 Flash + Google Search Grounding</sub>
</p>
