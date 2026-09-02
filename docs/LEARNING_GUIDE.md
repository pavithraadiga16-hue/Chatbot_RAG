# PhinsIQ Learning Guide

> **This guide is for you.** It starts from "What is Python backend?" and builds all the way up to understanding every component of PhinsIQ. Read it alongside the code.

---

## Table of Contents

1. [What is a Backend?](#1-what-is-a-backend)
2. [What is HTTP?](#2-what-is-http)
3. [What is an API?](#3-what-is-an-api)
4. [What is JSON?](#4-what-is-json)
5. [What is FastAPI?](#5-what-is-fastapi)
6. [What is async/await?](#6-what-is-asyncawait)
7. [What is MongoDB?](#7-what-is-mongodb)
8. [What is Middleware?](#8-what-is-middleware)
9. [What is Dependency Injection?](#9-what-is-dependency-injection)
10. [What is a Router?](#10-what-is-a-router)
11. [What is a Repository?](#11-what-is-a-repository)
12. [What is an Adapter?](#12-what-is-an-adapter)
13. [What is an Intent?](#13-what-is-an-intent)
14. [What is an Execution Plan?](#14-what-is-an-execution-plan)
15. [What is Field Extraction?](#15-what-is-field-extraction)
16. [What is Claude Fallback?](#16-what-is-claude-fallback)
17. [The PhinsIQ Request Lifecycle](#17-the-phinsiq-request-lifecycle)
18. [What is the Local Subject Engine (Math & Science)?](#18-what-is-the-local-subject-engine-math--science)

---


## 1. What is a Backend?

Imagine a restaurant.

- **The customer** = The user (student, staff)
- **The menu** = What the user can ask
- **The waiter** = The API (takes orders, brings food)
- **The kitchen** = The backend (processes requests, prepares answers)
- **The ingredients** = The ERP data (attendance records, fee data)
- **The recipe book** = PhinsIQ's configuration (how to make each dish)

The **backend** is software that runs on a **server** (a computer in a data center, not the user's phone). Users never see the backend code — only the results.

When a student's Flutter app asks "What is my attendance?", that request travels over the internet to PhinsIQ's backend server. The backend processes the request and sends back an answer. The Flutter app displays it.

**PhinsIQ's backend responsibilities:**
- Receive the question from any client (Flutter, website, etc.)
- Understand what the student is asking
- Know which institution they belong to
- Call the right ERP API
- Extract the right information
- Return a human-readable answer

---

## 2. What is HTTP?

**HTTP (HyperText Transfer Protocol)** is the language computers use to communicate over the internet.

Think of it like sending letters:
- **You write a letter** = HTTP Request
- **You specify the address** = URL
- **You write the subject** = HTTP Method
- **The letter content** = Request Body
- **The reply you receive** = HTTP Response
- **The reply's status** = HTTP Status Code

### HTTP Methods

| Method | Real-world analogy | PhinsIQ use |
|--------|--------------------|------------|
| `GET` | "Give me information" | Fetch health status |
| `POST` | "Here's information, do something with it" | Send a chat question |
| `PUT` | "Replace this with that" | Update institution config |
| `DELETE` | "Remove this" | Delete a record |

### HTTP Status Codes

| Code | Meaning | PhinsIQ example |
|------|---------|----------------|
| `200` | OK — success | Chat answered |
| `201` | Created — new resource made | — |
| `400` | Bad Request — your request is malformed | — |
| `401` | Unauthorized — who are you? | No token |
| `403` | Forbidden — I know you, but no | Student accessing payroll |
| `404` | Not Found | Unknown institution |
| `422` | Unprocessable — validation failed | Empty message |
| `500` | Internal Server Error — we broke | Unhandled exception |
| `503` | Service Unavailable | ERP or MongoDB down |

---

## 3. What is an API?

An **API (Application Programming Interface)** is a contract between two systems.

PhinsIQ defines this contract:
> "Send me a POST request to `/api/v1/phinsiq/chat` with this JSON body, and I'll send back an answer."

Any client — Flutter app, website, another server — can use PhinsIQ as long as they follow this contract. The client doesn't need to know:
- What language PhinsIQ is written in
- How PhinsIQ connects to MongoDB
- Which ERP APIs PhinsIQ calls
- Whether Claude was involved

This is the beauty of APIs: **implementation is hidden behind the contract.**

**PhinsIQ's chat API contract:**
```
POST /api/v1/phinsiq/chat
Content-Type: application/json

{
    "institution_id": "sags_school",
    "role": "student",
    "user_id": "ST123",
    "message": "What is my attendance?"
}
```

Response:
```json
{
    "success": true,
    "message": "Your current attendance is 94.7%."
}
```

---

## 4. What is JSON?

**JSON (JavaScript Object Notation)** is a universal data format that all programming languages understand.

```json
{
    "name": "Arjun",
    "roll_number": "ST123",
    "attendance_percentage": 94.7,
    "is_active": true,
    "subjects": ["Maths", "Science", "English"]
}
```

Rules:
- Keys must be **strings** (in double quotes)
- Values can be: string, number, boolean, array, object, null
- No trailing commas
- No comments

In Python, JSON maps directly to dictionaries:
```python
data = {
    "name": "Arjun",
    "attendance_percentage": 94.7,
    "is_active": True,  # Python uses True/False, JSON uses true/false
}
```

---

## 5. What is FastAPI?

FastAPI is a Python framework (a toolkit) for building APIs.

Without FastAPI, you'd have to write code to:
- Parse the raw HTTP request bytes
- Extract JSON from the body
- Validate each field
- Route to the right function
- Serialize the response back to JSON bytes
- Handle errors

FastAPI does ALL of this automatically. You just write:

```python
@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # By the time this runs:
    # - HTTP body has been read
    # - JSON has been parsed
    # - ChatRequest has been validated
    # - All fields are correct types
    return ChatResponse(success=True, message="Hello!")
```

**FastAPI also automatically generates interactive documentation** at `/docs`. You can test every API endpoint from your browser without writing any frontend code.

### The FastAPI Request Flow

```
Client → uvicorn → FastAPI middleware → route handler → your code
                                                       ↓
Client ← uvicorn ← FastAPI ← response serialization ← return value
```

---

## 6. What is async/await?

This is one of the most important concepts for PhinsIQ.

### The Problem: Blocking I/O

Imagine a waiter in a restaurant:

**Without async (synchronous):**
1. Take order from Table 1
2. Walk to kitchen
3. **STAND AND WAIT** for Table 1's food to cook (5 minutes)
4. Bring food to Table 1
5. Take order from Table 2 (Table 2 waited 5 minutes to even order!)

This is wasteful. The waiter is doing nothing while waiting.

**With async:**
1. Take order from Table 1
2. Submit order to kitchen
3. Take order from Table 2 (kitchen is cooking Table 1's food)
4. Bring water to Table 3
5. Kitchen signals: Table 1 ready → bring food

The waiter handles multiple tables efficiently because they don't stand idle waiting.

### In Python Terms

```python
# Synchronous (blocking) — BAD for PhinsIQ
def get_attendance():
    result = requests.get("http://erp.sags.edu/attendance")  # Python FREEZES here
    return result.json()

# Asynchronous (non-blocking) — GOOD for PhinsIQ
async def get_attendance():
    result = await httpx_client.get("http://erp.sags.edu/attendance")  # Python handles other requests while waiting
    return result.json()
```

### The Event Loop

The **event loop** is the coordinator — like the restaurant manager:
- It tracks all pending operations (waiting for ERP, waiting for MongoDB)
- When one completes, it resumes the function that was waiting
- In the meantime, it handles other incoming requests

FastAPI uses an event loop automatically. You just need to:
1. Mark functions as `async def` when they do I/O operations
2. Use `await` before any async operation

**When to use async in PhinsIQ:**
- ✅ Calling ERP APIs (network I/O)
- ✅ Querying MongoDB (database I/O)
- ✅ Route handlers (always async for consistency)
- ❌ Pure CPU computation (text processing, string matching)
- ❌ Simple helper functions with no I/O

---

## 7. What is MongoDB?

MongoDB is a **document database** — it stores data as JSON-like documents instead of rows and tables.

### Comparison: MySQL (ERP) vs MongoDB (PhinsIQ)

**MySQL (what the ERP uses):**
```sql
-- Rigid schema — every row must have the same columns
SELECT * FROM students WHERE id = 'ST123';
```

**MongoDB (what PhinsIQ uses):**
```json
// Flexible schema — each document can have different fields
{
    "_id": "sags_school",
    "name": "SAGS School",
    "status": "active",
    "roles": ["student", "staff"],
    "contact_email": "admin@sags.edu"   // optional field
}
```

### Why MongoDB for PhinsIQ?

PhinsIQ stores **configuration data** — not student data. Configuration is:
- Hierarchical (institution → role → module → action → field)
- Different for each institution
- Frequently changing as we add new institutions

MongoDB's flexible document structure is perfect for this.

### MongoDB Terminology

| MongoDB | SQL equivalent |
|---------|----------------|
| Database | Database |
| Collection | Table |
| Document | Row |
| Field | Column |
| `_id` | Primary key |

### PhinsIQ's Collections

```
phinsiq database
├── institutions    — Which institutions PhinsIQ supports
├── roles           — Which roles exist and their allowed modules
├── modules         — Module definitions
├── actions         — Actions within each module
├── fields          — Field definitions with aliases
├── api_registry    — Institution-specific ERP API configurations
├── templates       — Response template strings
├── claude_learning — Questions that needed Claude (training data)
└── analytics       — Request statistics
```

---

## 8. What is Middleware?

Middleware is code that runs **between** every request and your route handler.

Think of it like a security checkpoint at an office building:
- You arrive (request comes in)
- Security checks your ID (authentication middleware)
- Logs your entry time (logging middleware)
- Checks if you're allowed in this wing (CORS middleware)
- Then you reach your destination (route handler)

```
Request → Middleware 1 → Middleware 2 → Middleware N → Route Handler
Response ← Middleware 1 ← Middleware 2 ← Middleware N ← Route Handler
```

**PhinsIQ's middleware stack:**

1. **CORS Middleware** — Allows the browser demo UI to call the API
2. **Rate Limiting** (Phase 2) — Max 30 requests per minute per user
3. **Request ID** (future) — Assign a unique ID to every request for logging
4. **Authentication** (future) — Verify JWT tokens

---

## 9. What is Dependency Injection?

Dependency Injection (DI) is a pattern where a function declares what it needs, and the framework provides it.

**Without DI:**
```python
async def chat():
    db = get_database()        # Every function gets its own db
    config = load_config()     # Every function loads config
    logger = create_logger()   # Every function creates logger
    # ... actual work
```

**With DI (FastAPI style):**
```python
async def chat(
    request: ChatRequest,      # FastAPI injects the parsed request body
    db: Database = Depends(get_database),  # FastAPI injects the database
):
    # db is already there — you didn't have to get it
    # ... actual work
```

**Benefits:**
1. **Testability** — In tests, you can inject a fake database
2. **No repetition** — Database connection code is in one place
3. **Clarity** — Function signature tells you exactly what it needs

**PhinsIQ uses DI for:**
- Getting the MongoDB database instance
- Getting the authenticated user context
- Getting the institution configuration
- Rate limiting checks

---

## 10. What is a Router?

A router is a map from URLs to functions.

```python
# Without a router, you'd have to check URLs manually:
if path == "/health":
    return health_handler()
elif path == "/chat":
    return chat_handler()
```

FastAPI's router does this automatically:
```python
router = APIRouter()

@router.get("/health")     # GET /health → this function
async def health():
    return {"status": "ok"}

@router.post("/chat")      # POST /chat → this function
async def chat(request: ChatRequest):
    return ChatResponse(...)
```

**PhinsIQ's router hierarchy:**
```
app (FastAPI)
└── /api/v1 (v1 router)
    ├── GET  /health      (health router)
    └── POST /phinsiq/chat (chat router)
```

This hierarchy lets us version the API. When we build v2, we mount a new `/api/v2` router without breaking v1 clients.

---

## 11. What is a Repository?

A **repository** is a module dedicated to database operations for one type of data.

Instead of scattering MongoDB queries throughout the codebase:
```python
# BAD — MongoDB query inside business logic
async def process_request(institution_id: str):
    db = get_database()
    institution = await db.institutions.find_one({"_id": institution_id})  # DB query here!
    role = await db.roles.find_one({"_id": request.role})  # Another DB query!
    # ... more queries mixed with business logic
```

We separate them:
```python
# GOOD — Repository handles all DB operations
class InstitutionRepository:
    async def find_by_id(self, institution_id: str) -> dict | None:
        return await self.db.institutions.find_one({"_id": institution_id})

class RoleRepository:
    async def find_by_id(self, role_id: str) -> dict | None:
        return await self.db.roles.find_one({"_id": role_id})

# Business logic only calls repositories
async def process_request(institution_id: str):
    institution = await institution_repo.find_by_id(institution_id)
    role = await role_repo.find_by_id(request.role)
```

**Benefits:**
- One place to optimize MongoDB queries
- Easy to add caching (in the repository, not business logic)
- Easy to test (mock the repository, not MongoDB)

---

## 12. What is an Adapter?

Different institutions return data in different formats. An **adapter** normalizes them.

**SAGS School ERP returns:**
```json
{"attendance": 94.7}
```

**ABC College ERP returns:**
```json
{"attendancePercentage": 94.7}
```

**PhinsIQ's adapter configuration in MongoDB (`api_registry`):**
```json
{
  "institution_id": "sags_school",
  "response_mapping": {
    "percentage": "attendance"
  }
}
{
  "institution_id": "abc_college",
  "response_mapping": {
    "percentage": "attendancePercentage"
  }
}
```

**The adapter code:**
```python
def adapt_response(raw_response: dict, mapping: dict) -> dict:
    """
    Translates institution-specific field names to PhinsIQ's standard names.
    mapping = {"phinsiq_name": "erp_field_name"}
    """
    return {
        phinsiq_name: raw_response.get(erp_field)
        for phinsiq_name, erp_field in mapping.items()
    }

# Both institutions produce the same output:
# {"percentage": 94.7}
```

This is why PhinsIQ can support 150+ institutions with **zero institution-specific code**.

---

## 13. What is an Intent?

**Intent** is what the user *wants to do*, not what they literally said.

```
User says:    "Hey what's my attendance like these days?"
User means:   Fetch current attendance percentage
Intent:       module=attendance, action=percentage
```

PhinsIQ detects intent through several components:

### module_detector.py
Determines which ERP module the question is about.

```
"attendance" words: attend, present, absent, bunk, percentage, class
"fees" words: fee, pay, paid, pending, balance, due, challan
"exam" words: exam, test, result, marks, grade, score
```

### action_detector.py
Determines what to do with that module.

```
attendance + "how much" → percentage
attendance + "when was I absent" → absent_dates
fees + "how much" → pending_amount
fees + "full details" → complete_summary
```

### field_detector.py
Determines which specific fields to extract from the ERP response.

```
"pending fee" → field: pending
"total and paid" → fields: [total, paid]
"complete fee details" → fields: [total, paid, pending, discount]
```

---

## 14. What is an Execution Plan?

After understanding the intent, PhinsIQ creates an **execution plan** — a structured list of tasks to perform.

**Single question:**
```
"What is my attendance?"
↓
Plan:
{
    "tasks": [
        {
            "module": "attendance",
            "action": "percentage",
            "fields": ["percentage"],
            "filters": {}
        }
    ]
}
```

**Multi-part question:**
```
"Show my attendance and pending fee."
↓
Plan:
{
    "tasks": [
        {
            "module": "attendance",
            "action": "percentage",
            "fields": ["percentage"]
        },
        {
            "module": "fees",
            "action": "summary",
            "fields": ["pending"]
        }
    ]
}
```

PhinsIQ then:
1. Executes each task (calls the relevant ERP API)
2. Collects the results
3. Combines them into a single response

---

## 15. What is Field Extraction?

The ERP might return a large JSON response:
```json
{
    "student_id": "ST123",
    "total_fee": 50000,
    "paid_fee": 35000,
    "pending_fee": 15000,
    "discount": 5000,
    "next_due_date": "2026-09-15",
    "bank_details": {...}
}
```

If the student asked "What is my pending fee?", we **only extract** `pending_fee`:
```
{"pending_fee": 15000}
```

We do NOT:
- Send all this data to Claude
- Return all fields to the user
- Store any of this data

We extract only what was asked for and discard the rest.

---

## 16. What is Claude Fallback?

Claude is **not** the core of PhinsIQ. It is the safety net.

The pipeline tries deterministic logic first:
1. Is it a greeting? → Handle directly
2. Can we detect the module? → Yes → ERP API → Done
3. Can we detect the module? → No (confidence too low) → **Claude fallback**

**When Claude is called:**
- Complex reasoning ("Can I still reach 75% attendance?")
- Comparison questions ("Am I doing better than last month?")
- Unknown intent (the user said something we can't map to any module)
- Analysis ("Which subject am I struggling in?")

**What we send to Claude (minimum context):**
```
User question: "Can I still reach 75% attendance?"

Context:
- Student at SAGS School
- Current attendance: 65%
- Remaining classes: 40
- Total classes: 200

Please answer the student's question.
```

We do NOT send the entire ERP response. We fetch only the relevant data first.

**Claude Learning:**
Every time Claude is used, we record the question. This becomes training data to improve PhinsIQ's deterministic detection over time.

---

## 17. The PhinsIQ Request Lifecycle

Here's what happens when a student sends "What is my attendance?":

```
1. Flutter app → POST /api/v1/phinsiq/chat (JSON body)

2. uvicorn receives the TCP connection

3. FastAPI middleware:
   - CORS check (is this origin allowed?)
   - Rate limit check (has this user made too many requests?)

4. FastAPI validates ChatRequest:
   - institution_id, role, user_id, message all present?
   - message not empty, not too long?

5. chat() route handler receives the validated request

6. Pipeline starts:
   
   a. Pre-processing:
      - Is it a greeting? → Return "Hello! How can I help?" (STOP)
      - Is it profanity? → Return safe response (STOP)
      - Normalize text (lowercase, remove extra spaces)

   b. Request Understanding:
      - module_detector → "attendance" (confidence: 0.95)
      - action_detector → "percentage" (confidence: 0.92)
      - field_detector  → ["percentage"]
      - confidence.py   → overall: 0.94 (above threshold)

   c. Request Planning:
      - Create execution plan: [{module: "attendance", action: "percentage"}]

   d. Permission Check:
      - Student role allowed for "attendance" module? YES

   e. ERP API Routing:
      - Look up api_registry for sags_school/student/attendance/percentage
      - Build request: GET /api/student/attendance with user_id=ST123
      - Call ERP API asynchronously
      - Receive: {"attendancePercentage": 94.7}

   f. Response Mapping:
      - Apply adapter: {"attendancePercentage": 94.7} → {"percentage": 94.7}

   g. Response Generation:
      - Look up template: "Your current attendance is {percentage}%."
      - Fill in: "Your current attendance is 94.7%."

7. Return ChatResponse:
   {
     "success": true,
     "message": "Your current attendance is 94.7%.",
     "metadata": {"claude_used": false, "detected_module": "attendance"}
   }

8. Flutter app displays: "Your current attendance is 94.7%."
```

**Total time: ~200ms** (network + ERP API time)
**Claude used: No**
**Data sent to Claude: Nothing**

This is the PhinsIQ philosophy in action.

---

## 18. What is the Local Subject Engine (Math & Science)?

PhinsIQ goes beyond administrative ERP data (fees, attendance, homework) to solve **academic questions locally** across Mathematics, Physics, Chemistry, and Biology from LKG through PUC (Grade 12).

### Why a Local Engine?
- **Zero API Cost:** Solved on the local FastAPI server without calling Claude or any cloud LLM.
- **Ultra-Fast Speed:** Mathematical and scientific calculations finish in **<5ms**.
- **100% Deterministic Accuracy:** Uses exact scientific and mathematical libraries (`SymPy`, `NumPy`, `Pint`) to guarantee zero arithmetic hallucinations.

### What is Included?

1. **Mathematics Engine (18 Specialized Solvers):**
   - Arithmetic, BODMAS, Fractions, Prime Factors, HCF/LCM
   - Linear equations, Polynomials, and Quadratic Equations ($ax^2+bx+c=0$)
   - 2D Geometry (Circles, Triangles, Pythagoras) & 3D Mensuration (Cylinders, Cones, Spheres)
   - Trigonometry standard angles & identities
   - Symbolic Calculus (Derivatives $\frac{d}{dx}$ & Definite/Indefinite Integrals $\int$)
   - Coordinate Geometry, Matrices, Determinants, and Systems of Linear Equations
   - Sequences & Series (AP and GP $n$-th term and sum)
   - Permutations ($nPr$), Combinations ($nCr$), Binomial expansions
   - Statistics (Mean, Median, Mode, Variance, Standard Deviation) & Probability
   - Financial Math (Simple & Compound Interest, EMI, Profit/Loss)
   - Pint Physical Unit Conversions (Length, Mass, Speed, Temperature, Volume, Data Bytes)

2. **Science Engine:**
   - **Physics:** Dynamic Kinematics ($F=ma$, $v=u+at$, $s=ut+\frac{1}{2}at^2$), Energy ($KE=\frac{1}{2}mv^2, PE=mgh$), Ohm's Law ($V=IR$), Wave equations ($v=f\lambda$), Echo sonar ($d=\frac{vt}{2}$), Lens power ($P=1/f$), and Digital Logic Gates truth tables (AND, OR, NOT, NAND, NOR, XOR).
   - **Chemistry:** 68+ common chemical compounds database ($H_2O, D_2O, NaCl, NaHCO_3, CaCO_3, C_6H_{12}O_6$, etc.), 118 periodic table elements, case-insensitive formula parser, deterministic reaction balancer ($2H_2+O_2\to 2H_2O$), and pH calculations ($pH=-\log_{10}[H^+]$).
   - **Biology:** Organelle ontology (Mitochondria, Chloroplast, Ribosomes), human physiology, genetics, and comparative difference tables (Mitosis vs Meiosis, Xylem vs Phloem, Arteries vs Veins, Plant vs Animal cell).

3. **Navigation Behavior:**
   - For all Mathematics and Science responses, `route` is returned as `"NA"` and `routes` as `["NA"]` because pure academic solutions do not transition to an administrative ERP screen.

