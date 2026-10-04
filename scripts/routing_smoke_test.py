"""Smoke test for the Two-Path Architecture (ERP + RAG).

Usage: python scripts/routing_smoke_test.py [base_url]
Requires the server to be running (uvicorn app.main:app).
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
ENDPOINT = f"{BASE}/api/v1/phinsiq/chat"

QUERIES = [
    ("ERP", "What is my fee balance?"),
    ("ERP", "How many days was I absent?"),
    ("ERP", "What is my CGPA?"),
    ("RAG", "What is the minimum attendance requirement?"),
    ("RAG", "What is the leave policy?"),
    ("RAG", "Explain Module 3."),
    ("MULTI ERP+ERP", "What is my fee balance and how many days was I absent?"),
    ("MULTI ERP+RAG", "What is my fee balance and what is the minimum attendance requirement?"),
    ("NO_MATCH", "Can you recommend a good Italian restaurant in downtown Paris?"),
]


def detect_route(meta: dict | None, sources, expected: str) -> str:
    meta = meta or {}
    resp_type = meta.get("response_type") or ""
    if expected.startswith("MULTI"):
        parts = []
        if any(w in (meta.get("detected_module") or "") for w in ("fees", "attendance", "exam", "profile")):
            parts.append("ERP")
        if sources or resp_type == "multi_intent":
            parts.append("RAG")
        return "+".join(parts) or "?"
    if sources or resp_type == "rag":
        return "RAG"
    if meta.get("detected_module") and resp_type == "erp":
        return "ERP"
    if resp_type == "rag_no_match":
        return "NO_MATCH"
    return resp_type or "?"


def main() -> int:
    failures = 0
    for expected, question in QUERIES:
        try:
            resp = httpx.post(
                ENDPOINT,
                json={
                    "institution_id": "sjbhs",
                    "role": "student",
                    "user_id": "868",
                    "message": question,
                },
                timeout=30,
            )
            data = resp.json()
            meta = data.get("metadata") or {}
            sources = data.get("sources")
            route = detect_route(meta, sources, expected)
            ok = data.get("success")
            snippet = (data.get("message") or "").replace("\n", " ")[:110]
            print(f"Q: {question}")
            print(f"  expected={expected} | detected={route} | success={ok} | "
                  f"response_type={meta.get('response_type')} | module={meta.get('detected_module')} | "
                  f"sources={sources}")
            print(f"  A: {snippet}")
            if not ok:
                failures += 1
        except Exception as e:
            print(f"Q: {question} -> Request failed: {e}")
            failures += 1
    print(f"\n{len(QUERIES) - failures}/{len(QUERIES)} tests completed successfully")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
