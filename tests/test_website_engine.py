"""
Website Knowledge Engine & Crawler Tests (Dynamic & DB-Driven)
=============================================================

Comprehensive test suite verifying:
1. Dynamic HTML extraction into full structured JSON documents.
2. Auto-generation of structured Q&A entities with rich NLP Aliases from page content.
3. Multi-tier RapidFuzz search matching on arbitrary schools and roles.
4. Chat pipeline execution for role='website' and ERP roles.
5. Admin REST API endpoints (GET, POST, DELETE, raw-json).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.website_engine.cleaner import html_cleaner
from app.website_engine.extractor import json_extractor
from app.website_engine.repository import website_repo
from app.website_engine.searcher import website_searcher
from app.website_engine.models import CrawledPage, KnowledgeSection, WebsiteQAItem


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
async def seed_dynamic_test_knowledge():
    """Dynamically extract and ingest pages into repository/MongoDB for test institution."""
    sample_html_home = """
    <html>
    <head><title>St. Joseph's Boys' High School - Official Website</title></head>
    <body>
        <main>
            <h1>Welcome to St. Joseph's Boys' High School</h1>
            <p>St. Joseph's Boys' High School (SJBHS) was established in 1858 in Bangalore.</p>
            <h2>School Motto & Heritage</h2>
            <p>The motto of the school is Fide et Labore, translating to Faith and Toil.</p>
            <h2>Principal's Desk</h2>
            <p>Fr. Norwin Pereira, SJ is the Principal of St. Joseph's Boys' High School.</p>
            <h2>Campus Facilities & Abilities</h2>
            <p>The institution abilities include an Olympic-sized 25m swimming pool, synthetic football turf, cricket nets, modern science laboratories, and high-tech AI robotics rooms.</p>
            <h2>Notable Alumni</h2>
            <p>Famous alumni include Rahul Dravid, Sabeer Bhatia, and distinguished global leaders.</p>
        </main>
    </body>
    </html>
    """
    raw_json, qa_items = json_extractor.extract_full_json(
        html_content=sample_html_home,
        url="https://sjbhs.edu.in/",
        page_name="Home Page",
        institution_id="sjbhs",
        role="all",
    )

    page = CrawledPage(
        id="sjbhs_home_test",
        institution_id="sjbhs",
        page_name="Home Page",
        url="https://sjbhs.edu.in/",
        title="St. Joseph's Boys' High School - Official Website",
        status="success",
        role="all",
        category="General",
        raw_json_data=raw_json,
        qa_items=qa_items,
        sections=[
            KnowledgeSection(
                section_id="sec_1",
                institution_id="sjbhs",
                url="https://sjbhs.edu.in/",
                title="Principal and Leadership",
                content="Fr. Norwin Pereira, SJ is the Principal of St. Joseph's Boys' High School.",
                keywords=["principal", "leadership", "norwin pereira"],
            ),
            KnowledgeSection(
                section_id="sec_2",
                institution_id="sjbhs",
                url="https://sjbhs.edu.in/",
                title="Campus Facilities and Abilities",
                content="The institution abilities include an Olympic-sized 25m swimming pool, synthetic football turf, cricket nets, modern science laboratories.",
                keywords=["facilities", "swimming pool", "abilities", "sports"],
            ),
        ]
    )

    await website_repo.save_crawled_pages("sjbhs", [page])


# =============================================================================
# 1. HTML CLEANER & EXTRACTOR TESTS
# =============================================================================

def test_html_cleaner_strips_boilerplate():
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SJBHS Home - Official Portal</title>
        <meta name="description" content="St Joseph's Boys High School Bangalore">
        <script>console.log("analytics");</script>
        <style>.header { color: red; }</style>
    </head>
    <body>
        <nav class="navbar main-nav">
            <a href="/">Home</a><a href="/about">About</a>
        </nav>
        <div class="cookie-banner-popup">
            <p>Accept our cookies.</p>
        </div>
        <main>
            <h1>Welcome to St. Joseph's Boys' High School</h1>
            <p>St. Joseph's Boys' High School was established in 1858 in Bangalore.</p>
            <h2>Our School Motto</h2>
            <p>The motto of the school is Fide et Labore, meaning Faith and Toil.</p>
        </main>
        <footer class="site-footer">
            <p>© 2026 SJBHS All rights reserved.</p>
        </footer>
    </body>
    </html>
    """
    doc = html_cleaner.clean(raw_html, fallback_title="SJBHS")
    assert "SJBHS Home" in doc.title
    assert "cookie" not in doc.full_clean_text.lower()
    assert "analytics" not in doc.full_clean_text.lower()
    assert "1858" in doc.full_clean_text
    assert "Fide et Labore" in doc.full_clean_text


# =============================================================================
# 2. STRUCTURED JSON & Q&A NLP ALIASES EXTRACTOR TESTS
# =============================================================================

def test_structured_json_extractor_generates_qa_and_aliases():
    raw_html = """
    <html>
    <head><title>Greenwood International Academy - Overview</title></head>
    <body>
        <main>
            <h1>Leadership & Principal Message</h1>
            <p>Dr. Eleanor Vance is the Principal of Greenwood International Academy.</p>
            <h2>School Motto & Vision</h2>
            <p>The Motto is Excellence in Action (meaning Striving for Perfection). Established in 1995.</p>
            <h2>Campus Abilities & Facilities</h2>
            <p>Greenwood provides high-tech AI robotics labs, Olympic swimming arena, and smart digital auditoriums.</p>
        </main>
    </body>
    </html>
    """
    json_doc, qa_items = json_extractor.extract_full_json(
        html_content=raw_html,
        url="https://greenwood.edu/overview",
        page_name="Overview",
        institution_id="greenwood",
        role="all",
    )

    assert json_doc["title"] == "Greenwood International Academy - Overview"
    assert len(json_doc["headings_tree"]) >= 3
    assert len(qa_items) >= 3

    # Check Principal Q&A and NLP Aliases
    principal_qa = next((q for q in qa_items if q.field_key == "principal"), None)
    assert principal_qa is not None
    assert "Eleanor Vance" in principal_qa.answer
    assert "who is principal" in principal_qa.aliases
    assert "who is the headmaster" in principal_qa.aliases

    # Check Motto Q&A
    motto_qa = next((q for q in qa_items if q.field_key == "motto"), None)
    assert motto_qa is not None
    assert "Excellence in Action" in motto_qa.answer
    assert "school motto" in motto_qa.aliases


# =============================================================================
# 3. MULTI-TIER RAPIDFUZZ SEARCHER TESTS (WHO IS PRINCIPAL, INSTITUTION ABILITY)
# =============================================================================

@pytest.mark.asyncio
async def test_search_who_is_principal_nlp_alias():
    queries = [
        "who is principal",
        "who is the principal",
        "who is the principal of sjbhs",
        "principal name",
        "who is the headmaster",
        "father principal",
        "who leads the school",
    ]
    for q in queries:
        hits = await website_searcher.search("sjbhs", q, top_k=1)
        assert len(hits) > 0, f"Failed for query: {q}"
        top_hit = hits[0]
        assert top_hit.relevance_score >= 0.55, f"Low score {top_hit.relevance_score} for {q}"
        assert top_hit.qa_item is not None
        assert "Norwin Pereira" in top_hit.qa_item.answer


@pytest.mark.asyncio
async def test_search_institution_ability_nlp_alias():
    queries = [
        "what is the institution ability",
        "institution ability",
        "institution abilities",
        "what are the institution abilities",
        "campus facilities",
        "what facilities are available",
        "sports and campus facilities",
    ]
    for q in queries:
        hits = await website_searcher.search("sjbhs", q, top_k=1)
        assert len(hits) > 0, f"Failed for query: {q}"
        top_hit = hits[0]
        assert top_hit.relevance_score >= 0.50, f"Low score {top_hit.relevance_score} for {q}"
        assert (
            (top_hit.qa_item and "swimming pool" in top_hit.qa_item.answer.lower())
            or (top_hit.section and "swimming pool" in top_hit.section.content.lower())
        )


@pytest.mark.asyncio
async def test_search_motto_nlp_alias():
    queries = [
        "what is school motto",
        "what is the motto of sjbhs",
        "motto meaning",
        "what does fide et labore mean",
    ]
    for q in queries:
        hits = await website_searcher.search("sjbhs", q, top_k=1)
        assert len(hits) > 0, f"Failed for query: {q}"
        top_hit = hits[0]
        assert top_hit.relevance_score >= 0.55
        assert "Fide et Labore" in (top_hit.qa_item.answer if top_hit.qa_item else top_hit.section.content)


# =============================================================================
# 4. CHAT PIPELINE INTEGRATION TESTS (ROLE="WEBSITE" & STUDENT)
# =============================================================================

def test_chat_pipeline_role_website_who_is_principal(client: TestClient):
    client.post("/api/v1/admin/website/qa", json={
        "id": "sjbhs_qa_principal",
        "institution_id": "sjbhs",
        "field_key": "principal",
        "category": "Leadership & Administration",
        "question": "Who is the Principal of St. Joseph's Boys' High School (SJBHS)?",
        "answer": "**Fr. Norwin Pereira, SJ** is the Principal of St. Joseph's Boys' High School (SJBHS).",
        "aliases": ["who is principal", "who is the principal", "principal name", "who is the headmaster", "head of school"],
        "role": "all",
        "is_active": True,
    })
    payload = {
        "institution_id": "sjbhs",
        "role": "website",
        "user_id": "visitor",
        "message": "who is principal"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "Principal" in data["message"]
    assert data["route"] == "NA"


def test_chat_pipeline_student_asking_institution_ability(client: TestClient):
    client.post("/api/v1/admin/website/qa", json={
        "id": "sjbhs_qa_facilities_abilities",
        "institution_id": "sjbhs",
        "field_key": "facilities_abilities",
        "category": "Facilities & Abilities",
        "question": "What facilities and institution abilities does SJBHS provide?",
        "answer": "SJBHS provides a 25m swimming pool, synthetic turf, and laboratories.",
        "aliases": ["what is the institution ability", "institution ability", "institution abilities", "campus facilities", "school facilities"],
        "role": "all",
        "is_active": True,
    })
    payload = {
        "institution_id": "sjbhs",
        "role": "student",
        "user_id": "ST123",
        "message": "what is the institution ability"
    }
    resp = client.post("/api/v1/phinsiq/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "swimming pool" in data["message"].lower() or "facilities" in data["message"].lower()
    assert data["route"] == "NA"


# =============================================================================
# 5. ADMIN REST API Q&A & NLP ALIASES ENDPOINT TESTS
# =============================================================================

def test_admin_website_get_qa_items(client: TestClient):
    resp = client.get("/api/v1/admin/website/qa?institution_id=sjbhs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["total_qa_items"] >= 3
    assert any(q["field_key"] == "principal" for q in data["items"])


def test_admin_website_save_and_delete_qa_item(client: TestClient):
    # 1. Create custom Q&A item with custom NLP aliases
    new_qa = {
        "id": "sjbhs_qa_transport_custom",
        "institution_id": "sjbhs",
        "field_key": "school_bus",
        "category": "Facilities & Abilities",
        "question": "What are the school bus and transport routes?",
        "answer": "SJBHS operates GPS-tracked air-conditioned school buses covering 15 routes across Bangalore.",
        "aliases": ["school bus routes", "bus transport", "how to commute", "transportation facility"],
        "role": "all",
        "source_url": "https://sjbhs.edu.in/transport",
        "page_name": "Transport",
        "is_active": True,
    }
    save_resp = client.post("/api/v1/admin/website/qa", json=new_qa)
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    assert save_data["success"] is True

    # 2. Test search against the newly created Q&A alias
    search_payload = {
        "institution_id": "sjbhs",
        "question": "tell me about school bus routes",
        "role": "all"
    }
    search_resp = client.post("/api/v1/admin/website/test-search", json=search_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["success"] is True
    assert "GPS-tracked" in search_data["answer"]["answer"]

    # 3. Delete the custom Q&A item
    del_resp = client.delete(f"/api/v1/admin/website/qa/sjbhs_qa_transport_custom?institution_id=sjbhs")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_admin_website_get_raw_json(client: TestClient):
    resp = client.get("/api/v1/admin/website/raw-json?institution_id=sjbhs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["total_documents"] >= 1
    assert "raw_json_data" in data["documents"][0]


def test_admin_website_crawl_endpoint_execution(client: TestClient):
    payload = {
        "institution_id": "greenwood_academy",
        "urls": [
            {
                "name": "About Us",
                "url": "https://example.com/about",
                "role": "all",
                "category": "General"
            }
        ]
    }
    resp = client.post("/api/v1/admin/website/crawl", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "total_urls_processed" in data
