# PhinsIQ

**Enterprise AI Middleware Platform** — Parrophins Private Limited

PhinsIQ intelligently routes natural language questions from students and staff to institution-specific ERP APIs, returning concise natural language answers. Claude AI is used only as a fallback for complex reasoning.

---

## Quick Start (Development)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env
# Edit .env with your MongoDB URL and other settings

# 4. Start the server
uvicorn app.main:app --reload --port 8000

# 5. Open the development console
open index.html   # macOS
# Or open index.html in any browser

# 6. View API documentation
open http://localhost:8000/docs
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Server health check |
| `POST` | `/api/v1/phinsiq/chat` | Main chat endpoint (ERP + Website Knowledge + Subject Engine + Claude Fallback) |
| `POST` | `/api/v1/admin/website/crawl` | Trigger async website crawling & semantic chunking into Knowledge DB |
| `GET` | `/api/v1/admin/website/pages` | List all crawled website pages for an institution |
| `GET` | `/api/v1/admin/website/knowledge` | View extracted semantic knowledge sections |
| `DELETE` | `/api/v1/admin/website/knowledge` | Clear institution website knowledge database |
| `POST` | `/api/v1/admin/website/test-search` | Direct search test against stored website knowledge |
| `POST` | `/api/v1/subject-engine/mathematics/solve` | Dedicated 18-engine local Mathematics solver |
| `POST` | `/api/v1/subject-engine/science/solve` | Dedicated local Science solver (Physics, Chemistry, Biology) |
| `POST` | `/api/v1/subject-engine/solve` | Universal academic solver with auto-detection |
| `GET` | `/api/v1/subject-engine/concepts` | Ontology concepts catalog query endpoint |

### Chat Request (`role: "website"`)
```json
{
  "institution_id": "sjbhs",
  "role": "website",
  "user_id": "ST123",
  "message": "tell me about sjbhs overview and history"
}
```

### Chat Response (`role: "website"`)
```json
{
  "success": true,
  "message": "### 🌐 **St. Joseph's Boys' High School (SJBHS) — Overview**\n\nSt. Joseph's Boys' High School (SJBHS) is a premier Jesuit Catholic educational institution located on Museum Road in Bangalore, Karnataka, India. Established in 1858...\n\n🔗 **Source:** [https://sjbhs.edu.in/overview](https://sjbhs.edu.in/overview)",
  "route": "NA",
  "routes": ["NA"],
  "suggestion_questions": [
    "What is the school motto and its meaning?",
    "Tell me about famous alumni of the institution",
    "What campus facilities and sports infrastructure are available?"
  ],
  "metadata": {
    "claude_used": false,
    "response_type": "website_knowledge",
    "source_url": "https://sjbhs.edu.in/overview"
  }
}
```

---

## Architecture

```text
Admin adds website URLs (e.g. https://sjbhs.edu.in/)
        ↓
Phinsiq Website Crawler (httpx)
        ↓
Read HTML pages
        ↓
Extract useful content & strip boilerplate (BeautifulSoup)
        ↓
Split into semantic sections & extract keywords
        ↓
Store in Phinsiq Knowledge DB (MongoDB website_knowledge)
        ↓
User asks question (role: "website")
        ↓
RapidFuzz search stored website knowledge
        ↓
FastAPI Answer (<10ms, ₹0 cost, zero Claude, route: "NA")
```

---

## Key Architectural Principles

1. **Python code defines BEHAVIOR** — MongoDB defines CONFIGURATION
2. **ERP is the source of truth** — PhinsIQ never duplicates ERP data
3. **Local Deterministic AI first** — Mathematics and Science solved locally (<5ms, ₹0 cost) without LLM dependency
4. **Claude is the FALLBACK** — not the primary engine
5. **Institution-specific behavior is CONFIGURATION** — never `if institution == "X"`
6. **Design for 150+ institutions from Day 1**

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python 3.14 | Runtime |
| FastAPI | High-performance async web framework |
| Uvicorn | ASGI server with uvloop |
| SymPy | Exact symbolic mathematics, calculus, and reaction balancing |
| Pint | Physical unit arithmetic and conversions |
| NumPy | Linear algebra, matrices, numerical computing |
| RapidFuzz | C++ accelerated Levenshtein string & semantic ontology matching |
| Motor | Async MongoDB driver |
| HTTPX | Async HTTP client (ERP calls) |
| Structlog | Structured JSON logging |
| Jinja2 | Dynamic response templating |
| Pytest | Automated test suite (171 / 171 tests passed - 100%) |

