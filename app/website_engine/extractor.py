"""
Structured JSON & Knowledge Q&A Extractor (Dynamic & Generic)
=============================================================

Extracts complete web page content into a clean, structured JSON document
and automatically synthesizes high-precision Q&A entities with rich NLP Aliases
(what users can say to trigger each answer) for instant RapidFuzz search matching.

Works generically for ANY institution, school, college, university, or client website.
No hardcoded institution names or sample data.
"""

import hashlib
import re
from typing import Any, Optional
from bs4 import BeautifulSoup
from app.core.logging import get_logger
from app.website_engine.models import KnowledgeSection, WebsiteQAItem

logger = get_logger(__name__)


class StructuredJsonExtractor:
    """Extracts structured JSON hierarchies, institutional entities, and Q&A items with NLP aliases."""

    def extract_full_json(
        self,
        html_content: str,
        url: str,
        page_name: str,
        institution_id: str,
        role: str = "all",
    ) -> tuple[dict[str, Any], list[WebsiteQAItem]]:
        """
        Parse raw/cleaned HTML and extract complete structured JSON document + Q&A items.

        Args:
            html_content: HTML document string
            url: Page URL
            page_name: Friendly page name
            institution_id: Client institution ID (e.g. 'sjbhs', 'greenwood', 'harvard')
            role: Target role ('all', 'website', 'student', 'parent', 'staff')

        Returns:
            Tuple of (raw_json_data dict, list of WebsiteQAItem objects)
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Page Title & Meta
        title = ""
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text():
            title = title_tag.get_text().strip()
        if not title:
            h1 = soup.find("h1")
            if h1 and h1.get_text():
                title = h1.get_text().strip()
        if not title:
            title = page_name or "Official Page"

        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content").strip()

        # 2. Extract Headings & Nested Content
        headings_tree: list[dict[str, Any]] = []
        current_block: dict[str, Any] = {
            "heading": title,
            "level": "h1",
            "paragraphs": [],
            "bullets": [],
        }

        target_root = soup.find("main") or soup.find("article") or soup.body or soup

        for el in target_root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "table", "blockquote"]):
            tag = el.name.lower()
            text = re.sub(r"\s+", " ", el.get_text(strip=True)).strip()
            if not text:
                continue

            if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if current_block["paragraphs"] or current_block["bullets"]:
                    headings_tree.append(current_block)
                current_block = {
                    "heading": text,
                    "level": tag,
                    "paragraphs": [],
                    "bullets": [],
                }
            elif tag == "p":
                if len(text) > 8:
                    current_block["paragraphs"].append(text)
            elif tag in ["ul", "ol"]:
                items = [re.sub(r"\s+", " ", li.get_text(strip=True)) for li in el.find_all("li")]
                valid_items = [i for i in items if len(i) > 3]
                if valid_items:
                    current_block["bullets"].extend(valid_items)

        if current_block["paragraphs"] or current_block["bullets"]:
            headings_tree.append(current_block)

        # 3. Extract Contacts & Generic Entities from Page Text
        full_text = target_root.get_text(separator=" ", strip=True)
        emails = list(dict.fromkeys(re.findall(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", full_text)))
        phones = list(dict.fromkeys(re.findall(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{2,5}\)?[- ]?\d{3,5}[- ]?\d{3,5}\b", full_text)))

        extracted_entities = self._extract_named_entities(full_text)

        # Build raw JSON structure
        raw_json_data = {
            "institution_id": institution_id,
            "page_name": page_name,
            "url": url,
            "role": role,
            "title": title,
            "meta_description": meta_desc,
            "headings_count": len(headings_tree),
            "headings_tree": headings_tree,
            "contact_details": {
                "emails": emails[:5],
                "phone_numbers": phones[:5],
            },
            "extracted_entities": extracted_entities,
        }

        # 4. Generate structured Q&A items with NLP aliases completely from data
        qa_items = self.generate_qa_items_from_json(
            json_data=raw_json_data,
            institution_id=institution_id,
            url=url,
            page_name=page_name,
            role=role,
        )

        return raw_json_data, qa_items

    def _extract_named_entities(self, text: str) -> dict[str, Any]:
        """Generic entity extraction using natural language pattern matching."""
        entities: dict[str, Any] = {}

        # 1. Principal / Headmaster / Director / Leadership
        leadership_pattern = (
            r"(?:Principal|Headmaster|Headmistress|Director|Dean|Chancellor|Vice\s+Chancellor|"
            r"President|Chairman|Chairperson|Rector|Founder)\s*"
            r"(?:is|:|,|-|\s+of\s+(?:the\s+)?(?:school|college|institution|academy|university)\s+is)?\s*"
            r"(?:Fr\.|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}(?:,\s*SJ)?)"
        )
        lead_match = re.search(leadership_pattern, text, re.IGNORECASE)
        if lead_match:
            cand = lead_match.group(1).strip().rstrip(".,-")
            if len(cand) >= 3 and not re.search(r"\b(about|overview|history|facilities|admissions|curriculum|message)\b", cand, re.I):
                entities["principal"] = cand

        # 2. Motto / Vision / Slogan
        motto_pattern = (
            r"(?:Motto|School\s+Motto|Vision\s+Statement|Motto\s+of\s+the\s+School)\s*"
            r"(?:is|:|,|-)?\s*['\"]?([A-Za-z\s,]{3,60})['\"]?\s*"
            r"(?:\((?:meaning|translating\s+to|which\s+means)\s*['\"]?([^'\"\)]+)['\"]?\))?"
        )
        motto_match = re.search(motto_pattern, text, re.IGNORECASE)
        if motto_match:
            entities["motto"] = motto_match.group(1).strip()
            if motto_match.group(2):
                entities["motto_meaning"] = motto_match.group(2).strip()

        # 3. Established / Founding year
        est_match = re.search(
            r"(?:established|founded|started|origins\s+date\s+back\s+to|incepted|serving\s+since)\s*(?:in|since)?\s*(\b1[789]\d{2}\b|\b20\d{2}\b)",
            text,
            re.IGNORECASE
        )
        if est_match:
            entities["established_year"] = est_match.group(1)

        # 4. Affiliation / Board
        boards = re.findall(r"\b(ICSE|ISC|CBSE|State\s+Board|IGCSE|IB|Cambridge|State\s+Syllabus)\b", text, re.IGNORECASE)
        if boards:
            entities["board_curriculum"] = list(dict.fromkeys([b.upper() for b in boards]))

        return entities

    def _make_qa_id(self, institution_id: str, key: str) -> str:
        """Create a deterministic unique ID for a Q&A item."""
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", key.lower())[:35]
        hash_suffix = hashlib.md5(f"{institution_id}_{clean_key}".encode()).hexdigest()[:6]
        return f"{institution_id}_qa_{clean_key}_{hash_suffix}"

    def _generate_dynamic_aliases(self, topic: str, extra_triggers: Optional[list[str]] = None) -> list[str]:
        """Generate comprehensive natural language trigger variations for any topic."""
        aliases: list[str] = []
        topic_clean = re.sub(r"[^a-zA-Z0-9\s]", " ", topic.lower()).strip()
        topic_clean = re.sub(r"\s+", " ", topic_clean)

        if not topic_clean:
            return aliases

        aliases.append(topic_clean)
        aliases.append(f"what is {topic_clean}")
        aliases.append(f"what are {topic_clean}")
        aliases.append(f"tell me about {topic_clean}")
        aliases.append(f"details of {topic_clean}")
        aliases.append(f"{topic_clean} details")
        aliases.append(f"{topic_clean} info")
        aliases.append(f"{topic_clean} information")

        tokens = [t for t in topic_clean.split() if t not in {"and", "the", "for", "with", "from", "about", "what", "are", "our", "your"}]
        if len(tokens) >= 2:
            aliases.append(" ".join(tokens))

        if extra_triggers:
            aliases.extend(extra_triggers)

        # Deduplicate and return
        return list(dict.fromkeys([a.strip() for a in aliases if len(a.strip()) >= 2]))

    def generate_qa_items_from_json(
        self,
        json_data: dict[str, Any],
        institution_id: str,
        url: str,
        page_name: str,
        role: str = "all",
    ) -> list[WebsiteQAItem]:
        """
        Synthesize structured WebsiteQAItem entities with rich NLP Aliases from page JSON data.
        Generates items dynamically based strictly on extracted page content.
        """
        qa_items: list[WebsiteQAItem] = []
        inst_label = institution_id.replace("_", " ").title()

        entities = json_data.get("extracted_entities", {})
        headings = json_data.get("headings_tree", [])
        contacts = json_data.get("contact_details", {})

        # =========================================================================
        # 1. Leadership / Principal Entity (if present on page)
        # =========================================================================
        principal_name = entities.get("principal", "")
        # If not extracted directly, search headings for leadership blocks
        if not principal_name:
            for h in headings:
                h_name = h.get("heading", "").lower()
                if any(k in h_name for k in ["principal", "headmaster", "director", "dean", "leadership", "administration"]):
                    for p in h.get("paragraphs", []):
                        m = re.search(r"(?:Fr\.|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}(?:,\s*SJ)?)", p)
                        if m:
                            principal_name = m.group(0).strip().rstrip(".,-")
                            break
                    if principal_name:
                        break

        # Check if any heading is about the principal/headmaster
        has_lead_heading = any(
            any(k in h.get("heading", "").lower() for k in ["principal", "headmaster", "director", "head of school", "leadership message", "principal's desk"])
            for h in headings
        )

        if principal_name or has_lead_heading:
            lead_content = []
            for h in headings:
                if any(k in h.get("heading", "").lower() for k in ["principal", "headmaster", "director", "leadership"]):
                    lead_content.extend(h.get("paragraphs", []))
                    lead_content.extend([f"- {b}" for b in h.get("bullets", [])])

            lead_name_display = principal_name or "The Principal / Head of Institution"
            body_text = "\n\n".join(lead_content) if lead_content else f"**{lead_name_display}** oversees the leadership, academic governance, and institutional vision for {inst_label}."

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, "principal"),
                    institution_id=institution_id,
                    field_key="principal",
                    category="Leadership & Administration",
                    question=f"Who is the Principal / Head of {inst_label}?",
                    answer=f"**{lead_name_display}** is the Principal of {inst_label}.\n\n{body_text}",
                    aliases=self._generate_dynamic_aliases(
                        "principal",
                        extra_triggers=[
                            "who is principal",
                            "who is the principal",
                            "principal name",
                            "who is the headmaster",
                            "headmaster",
                            "head of school",
                            "father principal",
                            "director",
                            "who is the director",
                            "who leads the school",
                            "who leads the institution",
                            "school principal",
                            "contact principal",
                            "desk of principal",
                            f"principal of {institution_id}",
                            lead_name_display.lower(),
                        ]
                    ),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        # =========================================================================
        # 2. Motto & Values Entity (if present on page)
        # =========================================================================
        motto_text = entities.get("motto", "")
        meaning_text = entities.get("motto_meaning", "")
        has_motto_heading = any("motto" in h.get("heading", "").lower() or "vision" in h.get("heading", "").lower() for h in headings)

        if motto_text or has_motto_heading:
            motto_content = []
            for h in headings:
                if any(k in h.get("heading", "").lower() for k in ["motto", "vision", "mission", "values"]):
                    motto_content.extend(h.get("paragraphs", []))

            ans_str = ""
            if motto_text:
                ans_str = f"The motto of {inst_label} is **'{motto_text}'**"
                if meaning_text:
                    ans_str += f", which translates to **'{meaning_text}'**.\n\n"
                else:
                    ans_str += ".\n\n"
            if motto_content:
                ans_str += "\n\n".join(motto_content)

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, "motto"),
                    institution_id=institution_id,
                    field_key="motto",
                    category="About & Heritage",
                    question=f"What is the school motto and vision of {inst_label}?",
                    answer=ans_str or f"The vision and motto of {inst_label} centers on excellence and holistic education.",
                    aliases=self._generate_dynamic_aliases(
                        "school motto",
                        extra_triggers=[
                            "what is school motto",
                            "school motto",
                            "motto",
                            "what does school motto mean",
                            "motto meaning",
                            "motto of the school",
                            "motto of the institution",
                            "school slogan",
                            "school vision and motto",
                            f"motto of {institution_id}",
                            motto_text.lower() if motto_text else "",
                            meaning_text.lower() if meaning_text else "",
                        ]
                    ),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        # =========================================================================
        # 3. Established Year & History (if present on page)
        # =========================================================================
        est_year = entities.get("established_year", "")
        has_history_heading = any(any(k in h.get("heading", "").lower() for k in ["history", "heritage", "legacy", "about", "overview"]) for h in headings)

        if est_year or has_history_heading:
            hist_content = []
            for h in headings:
                if any(k in h.get("heading", "").lower() for k in ["history", "heritage", "legacy", "about", "overview", "founded"]):
                    hist_content.extend(h.get("paragraphs", []))
                    hist_content.extend([f"- {b}" for b in h.get("bullets", [])])

            est_lead = f"{inst_label} was established in **{est_year}**.\n\n" if est_year else ""
            hist_ans = est_lead + ("\n\n".join(hist_content) if hist_content else f"{inst_label} has a rich heritage of academic and holistic excellence.")

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, "history_overview"),
                    institution_id=institution_id,
                    field_key="history_overview",
                    category="About & Heritage",
                    question=f"When was {inst_label} founded and what is its history?",
                    answer=hist_ans,
                    aliases=self._generate_dynamic_aliases(
                        "school history",
                        extra_triggers=[
                            "when was school founded",
                            "when was institution founded",
                            "tell me about school history",
                            "school history",
                            "institution history",
                            "founding year",
                            "establishment year",
                            f"when was {institution_id} established",
                            "history and overview",
                            "overview of the school",
                            "about the school",
                            "heritage of the school",
                            est_year if est_year else "",
                        ]
                    ),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        # =========================================================================
        # 4. Campus Abilities & Facilities (if present on page)
        # =========================================================================
        facility_keywords = ["facility", "facilities", "campus", "sports", "swimming", "laboratory", "auditorium", "infrastructure", "ability", "abilities", "amenities", "grounds", "library", "labs"]
        facility_headings = [h for h in headings if any(k in h.get("heading", "").lower() for k in facility_keywords)]

        if facility_headings:
            fac_content = []
            fac_items = []
            for fh in facility_headings:
                fac_content.extend(fh.get("paragraphs", []))
                for b in fh.get("bullets", []):
                    fac_items.append(f"- {b}")

            combined_fac = "\n\n".join(fac_content)
            if fac_items:
                combined_fac += "\n\n**Facilities & Campus Abilities:**\n" + "\n".join(fac_items)

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, "facilities_abilities"),
                    institution_id=institution_id,
                    field_key="facilities_abilities",
                    category="Facilities & Abilities",
                    question=f"What facilities and institution abilities does {inst_label} provide?",
                    answer=combined_fac or f"{inst_label} provides state-of-the-art campus infrastructure and facilities.",
                    aliases=self._generate_dynamic_aliases(
                        "institution ability",
                        extra_triggers=[
                            "what is the institution ability",
                            "institution ability",
                            "institution abilities",
                            "what are the institution abilities",
                            "campus facilities",
                            "school facilities",
                            "sports facilities",
                            "what facilities are available",
                            "campus infrastructure",
                            "infrastructure of the school",
                            "abilities of school",
                            "abilities of institution",
                            "labs and facilities",
                            "sports and campus facilities",
                        ]
                    ),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        # =========================================================================
        # 5. Admissions & Eligibility (if present on page)
        # =========================================================================
        adm_keywords = ["admission", "admissions", "apply", "enrollment", "eligibility", "fees", "fee structure", "how to apply"]
        adm_headings = [h for h in headings if any(k in h.get("heading", "").lower() for k in adm_keywords)]

        if adm_headings:
            adm_content = []
            for ah in adm_headings:
                adm_content.extend(ah.get("paragraphs", []))
                adm_content.extend([f"- {b}" for b in ah.get("bullets", [])])

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, "admissions"),
                    institution_id=institution_id,
                    field_key="admissions",
                    category="Admissions",
                    question=f"What is the admission procedure and criteria for {inst_label}?",
                    answer="\n\n".join(adm_content) or f"Admissions at {inst_label} follow the institutional guidelines and criteria.",
                    aliases=self._generate_dynamic_aliases(
                        "admissions",
                        extra_triggers=[
                            "how to get admission",
                            "admission process",
                            "admission criteria",
                            "admission fees",
                            "eligibility",
                            "admissions procedure",
                            "how to apply for admission",
                            f"admission in {institution_id}",
                        ]
                    ),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        # =========================================================================
        # 6. Contact Information & Location (if present on page)
        # =========================================================================
        if contacts.get("emails") or contacts.get("phone_numbers") or any("contact" in h.get("heading", "").lower() for h in headings):
            contact_lines = []
            if contacts.get("emails"):
                contact_lines.append(f"📧 **Email:** {', '.join(contacts['emails'])}")
            if contacts.get("phone_numbers"):
                contact_lines.append(f"📞 **Phone:** {', '.join(contacts['phone_numbers'])}")

            for h in headings:
                if "contact" in h.get("heading", "").lower() or "address" in h.get("heading", "").lower() or "location" in h.get("heading", "").lower():
                    contact_lines.extend(h.get("paragraphs", []))
                    contact_lines.extend([f"- {b}" for b in h.get("bullets", [])])

            if contact_lines:
                qa_items.append(
                    WebsiteQAItem(
                        id=self._make_qa_id(institution_id, "contact_details"),
                        institution_id=institution_id,
                        field_key="contact_details",
                        category="Contact & Location",
                        question=f"How to contact {inst_label} or visit the campus?",
                        answer="\n\n".join(contact_lines),
                        aliases=self._generate_dynamic_aliases(
                            "contact details",
                            extra_triggers=[
                                "contact number",
                                "school email",
                                "phone number",
                                "school address",
                                "how to contact",
                                "location",
                                "campus address",
                                "office phone number",
                                f"contact {institution_id}",
                            ]
                        ),
                        role=role,
                        source_url=url,
                        page_name=page_name,
                        is_active=True,
                    )
                )

        # =========================================================================
        # 7. Convert All Other Headings on Page to Structured Q&A with NLP Aliases
        # =========================================================================
        existing_keys = {q.field_key for q in qa_items}

        for idx, h in enumerate(headings):
            h_text = h.get("heading", "").strip()
            if not h_text:
                continue

            clean_slug = re.sub(r"[^a-z0-9]", "_", h_text.lower())[:24]
            if clean_slug in existing_keys or any(clean_slug in k for k in existing_keys):
                continue

            content_lines = h.get("paragraphs", []) + [f"- {b}" for b in h.get("bullets", [])]
            if not content_lines:
                continue

            sec_answer = "\n\n".join(content_lines)
            field_key = f"topic_{clean_slug}"
            existing_keys.add(clean_slug)

            qa_items.append(
                WebsiteQAItem(
                    id=self._make_qa_id(institution_id, f"heading_{idx}_{clean_slug}"),
                    institution_id=institution_id,
                    field_key=field_key,
                    category="General Information",
                    question=f"What is the information regarding '{h_text}' at {inst_label}?",
                    answer=sec_answer,
                    aliases=self._generate_dynamic_aliases(h_text),
                    role=role,
                    source_url=url,
                    page_name=page_name,
                    is_active=True,
                )
            )

        return qa_items


json_extractor = StructuredJsonExtractor()
