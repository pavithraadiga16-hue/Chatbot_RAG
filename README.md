# PhinsIQ

**Enterprise AI Middleware Platform** — Parrophins Private Limited

PhinsIQ is a high-performance, deterministic AI middleware platform that intelligently routes institution and student queries into a **strictly two-path architecture**:
1. **Existing ERP / API Path**: For real-time student-specific data (fee balance, attendance, absent days, CGPA, profile, marks, exams, schedule).
2. **Institutional Document RAG Path**: For uploaded institutional policies, lecturer notes, module materials, and academic PDFs.

There are **zero cloud LLM dependencies** (no Gemini, OpenAI, Claude, or Anthropic) and **no local LLM/Qwen dependencies**. When requested information is not found in either the ERP or uploaded documents, PhinsIQ returns a clean, transparent response rather than hallucinating answers.

---

## Final Two-Path Architecture

```text
                    USER QUERY
                         |
                         v
                REDIS CACHE CHECK
             (Student-Isolated Keys)
                   HIT / MISS
                         |
                         v
                   QUERY ROUTER
                         |
              ┌──────────┴──────────┐
              |                     |
              v                     v
        EXISTING ERP/API           RAG
      Student / System Data    PDFs / Notes / Policies
              |                     |
              └──────────┬──────────┘
                         |
                         v
                  FINAL RESPONSE
                         |
                         v
                 STORE REDIS CACHE
```

* **No Cloud LLM Path**: Zero external API calls to OpenAI, Claude, Gemini, or Anthropic.
* **No Qwen / Ollama Path**: Fully offline, deterministic extraction without background LLM daemons.
* **Strict Student Privacy**: Student-specific records are never mixed, stored in global cache keys, or shared.

---

## Quick Start (Development)

```bash
# 1. Activate virtual environment
source venv/bin/activate       # Linux/macOS
# .\venv\Scripts\Activate.ps1   # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env
# Edit .env with your MongoDB URL, Redis URL, and settings

# 4. Ingest and index institutional documents
python -m app.rag.ingestion

# 5. Start the server
python -m uvicorn app.main:app --reload --port 8000

# 6. Open the development console
open index.html   # macOS
# Or double-click index.html in any browser

# 7. View API documentation
open http://localhost:8000/docs
```

---

## RAG Document Ingestion & Management

### Document Location
All institutional documents, lecturer notes, and module PDFs live in one clear location:

```text
data/
└── rag/
    ├── documents/
    │   ├── module_1/           # e.g., Biology notes, Photosynthesis
    │   ├── module_2/           # e.g., Chemistry notes, PDFs
    │   ├── module_3/           # e.g., Physics notes, Lecture notes
    │   ├── module_4/           # e.g., Mathematics notes
    │   └── module_5/           # e.g., Examination & Policy PDFs
    └── index/
        └── rag.sqlite3         # SQLite vector & full-text search index
```

### Supported File Types
* **PDFs (`.pdf`)**: Extracted page-by-page via `pypdf`.
* **Plain Text (`.txt`)**: Read and chunked with utf-8 encoding.
* **Markdown (`.md`)**: Read and chunked with utf-8 encoding.

### Adding a New PDF or Lecturer Note
You can add new documents or modules at any time **without modifying application source code**:

1. **Place the file**:
   Save your new `.pdf`, `.txt`, or `.md` file into the target module folder, for example:
   ```text
   data/rag/documents/module_3/quantum_mechanics_lecture.pdf
   ```

2. **Run ingestion and indexing**:
   From the project root directory, run:
   ```bash
   python -m app.rag.ingestion
   ```

3. **Verify indexed chunks**:
   The ingestion script recursively parses all module directories, chunks the content with word-aligned overlapping windows, builds deterministic vector embeddings, and updates `data/rag/index/rag.sqlite3`.

---

## Query Routing & Processing

The Query Router inspects incoming natural language questions and routes them to the correct path:

| Query Type | Example Question | Processing Path | Source |
|------------|------------------|-----------------|--------|
| **Student Record** | "What is my fee balance?" | ERP / API Path | Live ERP / MongoDB |
| **Student Record** | "How many days was I absent?" | ERP / API Path | Live ERP / MongoDB |
| **Student Record** | "What is my CGPA?" | ERP / API Path | Live ERP / MongoDB |
| **Institutional Policy** | "What is the minimum attendance requirement?" | RAG Path | `attendance_policy.txt` |
| **Institutional Policy** | "What is the leave policy?" | RAG Path | `leave_policy.txt` |
| **Academic Note** | "Explain Module 3." | RAG Path | `module_3_lecture_notes.txt` |
| **Academic Note** | "Explain the topic from lecturer's notes." | RAG Path | Uploaded PDFs / notes |
| **Holiday / Calendar** | "Is there a holiday according to the calendar?" | ERP Calendar first, fallback to RAG | ERP / RAG Calendar |
| **Multi-Part ERP+ERP** | "What is my fee balance and how many days was I absent?" | Combined ERP Paths | Fees + Attendance ERP |
| **Multi-Part ERP+RAG** | "What is my fee balance and what is the minimum attendance requirement?" | Combined ERP + RAG | Fees ERP + Attendance RAG |
| **Unmatched Query** | "What is the cafeteria menu today?" | No-Match Response | Returns transparent message |

### Multi-Part Query Resolution
When a query contains multiple clauses (e.g. joined by "and", "also", or comma):
1. The router decomposes the query into sub-clauses.
2. Each sub-clause is classified as ERP or RAG.
3. The pipeline executes each handler (in parallel for ERP modules).
4. Both answers are combined into a single structured response with appropriate navigation routes and suggestion questions.

---

## Redis Caching & Student Data Isolation

PhinsIQ uses an asynchronous Redis caching layer with strict student identity scoping:

* **Student-Specific Queries (ERP)**:
  Cache keys include the institution and student's authenticated ID:
  ```text
  phinsiq:cache:student:{institution_id}:{user_id}:{normalized_query}
  ```
  Default TTL: 300 seconds (5 minutes). Student A will **never** receive cached data from Student B.

* **Institutional / Policy Queries (RAG)**:
  Shared institutional questions use institution-scoped keys:
  ```text
  phinsiq:cache:rag:{institution_id}:{normalized_query}
  ```
  Default TTL: 3600 seconds (1 hour).

* **Resilient Fallback**: If Redis is offline or unreachable, `CacheService` automatically switches to an in-memory TTL dictionary without throwing errors or interrupting service.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check endpoint |
| `POST` | `/api/v1/phinsiq/chat` | Main query endpoint (ERP + RAG + Redis Caching) |
| `POST` | `/api/v1/admin/website/crawl` | Website crawler for public school portal pages |
| `GET` | `/api/v1/admin/website/knowledge` | View crawled website Q&A items |
| `POST` | `/api/v1/subject-engine/mathematics/solve` | Dedicated local Mathematics engine |
| `POST` | `/api/v1/subject-engine/science/solve` | Dedicated local Science engine (Physics, Chemistry, Biology) |
| `POST` | `/api/v1/subject-engine/solve` | Generic subject engine solver |
| `GET` | `/api/v1/subject-engine/concepts` | Ontology concepts catalog query endpoint |

---

## Testing

Run the automated test suite with pytest:

```bash
# Run all tests
python -m pytest

# Run RAG tests
python -m pytest tests/test_rag.py

# Run Multi-Intent tests
python -m pytest tests/test_multi_intent.py tests/test_multi_intent_pipeline.py

# Run ERP module tests
python -m pytest tests/test_academic_overview.py tests/test_profile.py tests/test_calendar_holiday.py
```

---

## License

Proprietary — Parrophins Private Limited. All Rights Reserved.
