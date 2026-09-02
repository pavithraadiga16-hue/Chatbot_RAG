"""
Template Engine
================

PURPOSE:
    Converts structured ERP data into natural language responses
    using pre-defined templates from MongoDB.

    Input (from ERP, after mapping):
        {"pending_amount": 42500, "total_fee": 85000, "paid_amount": 42500}

    Requested fields: ["pending_amount"]

    Template: "Your pending fee amount is ₹{pending_amount}."

    Output: "Your pending fee amount is ₹42,500."

WHY TEMPLATES INSTEAD OF CLAUDE?
    1. FREE: Template rendering costs nothing. Claude costs per token.
    2. FAST: String substitution takes microseconds. Claude takes 1-3 seconds.
    3. CONSISTENT: Templates always produce the same format.
    4. CONTROLLABLE: Business owners can edit templates without touching code.

TEMPLATE TYPES:
    1. Field template: "Your {field_name} is ₹{value}."
       → Used when user asks for one specific field
    2. Summary template: Multi-line overview with multiple fields
       → Used when user asks for "all details" or no specific field detected
    3. Multi-field template: Lists multiple requested fields
       → Used when user asks for 2-3 specific fields

CURRENCY FORMATTING:
    We format currency values with commas: 85000 → 85,000
    This makes responses more readable for Indian users.
"""

from typing import Any, Optional
from app.core.logging import get_logger
from app.router.response_mapper import format_value

logger = get_logger(__name__)


class TemplateEngine:
    """
    Renders natural language responses from templates and ERP data.

    This class is the bridge between raw data and human-readable answers.
    """

    def render_single_field(
        self,
        field_name: str,
        value: Any,
        templates_doc: dict,
        field_format: str = "text",
    ) -> Optional[str]:
        """
        Render a response for a single requested field.

        Args:
            field_name:    PhinsIQ standard field name (e.g., "pending_amount")
            value:         Raw value from ERP or ArrayAggregator (int, float, str, list)
            templates_doc: Templates document from MongoDB
            field_format:  How to format the value ("currency", "percentage", "date_list", etc.)

        Returns:
            Rendered response string, or None if no template found.
        """
        field_templates = templates_doc.get("field_templates", {})
        template = field_templates.get(field_name)

        # For list-type values, use a specialized list renderer
        # even if no field template exists, to produce readable output.
        if isinstance(value, list):
            return self._render_list_field(field_name, value, template, field_format)

        if not template:
            logger.warning("no_template_for_field", field_name=field_name)
            return None

        # Format the value
        formatted_value = format_value(value, field_format)

        # Substitute the placeholder
        # Templates use {field_name} as placeholder: "Your pending fee is ₹{pending_amount}"
        rendered = template.replace(f"{{{field_name}}}", formatted_value)

        return rendered

    def _render_list_field(
        self,
        field_name: str,
        value: list,
        template: Optional[str],
        field_format: str,
    ) -> str:
        """
        Render a list-type field value (from ArrayAggregator) as a readable response.

        If a template exists with a {field_name} placeholder, substitute with
        comma-joined list. Otherwise, produce a numbered bullet list.

        WHY NUMBERED BULLETS?
            For absent dates: ["2026-06-08", "2026-06-22", ...]
            A numbered bullet list is more readable than one long comma string:

            Your absent dates are:
            1. 08 Jun 2026
            2. 22 Jun 2026
            ...
        """
        if not value:
            label = field_name.replace("_", " ").title()
            return f"No {label.lower()} found."

        # Format for inline substitution
        formatted_inline = format_value(value, field_format)

        # If a template is defined, use it with inline formatted value
        if template:
            return template.replace(f"{{{field_name}}}", formatted_inline)

        # No template — build a numbered bullet list for date_list and list formats
        label = field_name.replace("_", " ").title()
        if field_format in ("date_list", "list"):
            from app.router.response_mapper import _format_iso_date
            lines = [f"Here are your {label.lower()}:\n"]
            for i, item in enumerate(value, 1):
                # Try to format as date if date_list
                if field_format == "date_list":
                    display = _format_iso_date(str(item))
                else:
                    display = str(item)
                lines.append(f"{i}. {display}")
            return "\n".join(lines)

        return f"Your {label.lower()}: {formatted_inline}"

    def render_multi_field(
        self,
        field_data: dict[str, Any],
        templates_doc: dict,
        field_definitions: list[dict],
    ) -> str:
        """
        Render a response when the user requested 2 or more specific fields.

        For each field, we either use its specific template or fall back
        to a generic "Field: Value" format. List-type values (from
        ArrayAggregator) are formatted as count summaries in multi-field mode
        to keep the response concise.

        Args:
            field_data:        {field_name: value} dict of requested fields
            templates_doc:     Templates document from MongoDB
            field_definitions: Field defs from MongoDB (for labels and formats)

        Returns:
            Multi-line response string with all requested fields.
        """
        # Build a lookup for field metadata: {field_name: {label, format}}
        field_meta = {
            f["name"]: f for f in field_definitions
        }

        lines = []
        for field_name, value in field_data.items():
            meta = field_meta.get(field_name, {})
            label = meta.get("label", field_name.replace("_", " ").title())
            fmt = meta.get("format", "text")

            # For list-type values in multi-field mode, show count + summary
            if isinstance(value, list):
                count = len(value)
                formatted_inline = format_value(value, fmt)
                # Use template if available
                field_templates = templates_doc.get("field_templates", {})
                template = field_templates.get(field_name)
                if template:
                    rendered = template.replace(f"{{{field_name}}}", formatted_inline)
                    lines.append(rendered)
                else:
                    lines.append(f"**{label}:** {count} record(s) — {formatted_inline[:80]}{'...' if len(formatted_inline) > 80 else ''}")
                continue

            formatted = format_value(value, fmt)

            # Try to use field-specific template, fall back to "Label: Value"
            field_templates = templates_doc.get("field_templates", {})
            template = field_templates.get(field_name)

            if template:
                rendered = template.replace(f"{{{field_name}}}", formatted)
                lines.append(rendered)
        # If all rendered entries are single-line sentences/clauses,
        # combine them into a single flowing natural sentence:
        # e.g. "You have attended 51 day(s) so far, and you have been absent 10 time(s) so far."
        # e.g. "Your pending fee amount is ₹15,000, and your total fee for this term is ₹50,000."
        has_multiline = any("\n" in l for l in lines)
        if not has_multiline and lines:
            clean_clauses = []
            for line in lines:
                c = line.strip().rstrip(".")
                if clean_clauses and c:
                    words = c.split(" ", 1)
                    first = words[0]
                    # Lowercase starting pronoun/determiner for grammatical flow
                    if first.lower() in ("you", "your", "a", "the", "an", "installment", "total", "paid", "pending"):
                        c = first.lower() + (" " + words[1] if len(words) > 1 else "")
                clean_clauses.append(c)

            if len(clean_clauses) == 1:
                return clean_clauses[0] + "."
            elif len(clean_clauses) == 2:
                return f"{clean_clauses[0]}, and {clean_clauses[1]}."
            elif len(clean_clauses) >= 3:
                return ", ".join(clean_clauses[:-1]) + f", and {clean_clauses[-1]}."

        return "\n".join(lines)

    def render_summary(
        self,
        mapped_data: dict[str, Any],
        templates_doc: dict,
        field_definitions: list[dict],
    ) -> str:
        """
        Render a full summary response when user wants all data or no specific field.

        Uses the 'summary_template' from MongoDB if available.
        Falls back to generating a list of all available fields.

        Args:
            mapped_data:       Full mapped ERP response {field_name: value}
            templates_doc:     Templates document from MongoDB
            field_definitions: Field defs from MongoDB

        Returns:
            Multi-line summary response
        """
        summary_template = templates_doc.get("summary_template")

        if summary_template:
            # Replace all {field_name} placeholders in the summary template
            rendered = summary_template
            field_meta = {f["name"]: f for f in field_definitions}

            for field_name, value in mapped_data.items():
                if value is not None:
                    meta = field_meta.get(field_name, {})
                    fmt = meta.get("format", "text")
                    formatted = format_value(value, fmt)
                    rendered = rendered.replace(f"{{{field_name}}}", formatted)

            # Clean up any unreplaced placeholders (fields with None values)
            import re
            rendered = re.sub(r'\{[^}]+\}', 'N/A', rendered)
            return rendered

        # Fallback: generate a list of all non-null fields
        field_meta = {f["name"]: f for f in field_definitions}
        lines = ["Here are your details:\n"]
        for field_name, value in mapped_data.items():
            if value is not None:
                meta = field_meta.get(field_name, {})
                label = meta.get("label", field_name.replace("_", " ").title())
                fmt = meta.get("format", "text")
                formatted = format_value(value, fmt)
                if fmt == "currency":
                    lines.append(f"• {label}: ₹{formatted}")
                else:
                    lines.append(f"• {label}: {formatted}")

        return "\n".join(lines) if lines else "No information available."

    def render(
        self,
        requested_fields: list[str],
        wants_summary: bool,
        mapped_data: dict[str, Any],
        templates_doc: dict,
        field_definitions: list[dict],
    ) -> str:
        """
        Main render method — decides which render strategy to use.

        Logic:
            wants_summary=True OR no fields detected → render_summary()
            1 field requested → render_single_field()
            2+ fields requested → render_multi_field()

        Args:
            requested_fields:  List of field names the user asked for
            wants_summary:     True if user asked for all/complete data
            mapped_data:       Full mapped ERP response
            templates_doc:     MongoDB templates document
            field_definitions: MongoDB field definitions

        Returns:
            Final natural language response string
        """
        field_meta = {f["name"]: f for f in field_definitions}

        if wants_summary or not requested_fields:
            logger.debug("template_rendering_summary")
            return self.render_summary(mapped_data, templates_doc, field_definitions)

        elif len(requested_fields) == 1:
            field_name = requested_fields[0]
            value = mapped_data.get(field_name)
            fmt = field_meta.get(field_name, {}).get("format", "text")
            logger.debug("template_rendering_single_field", field=field_name)

            rendered = self.render_single_field(field_name, value, templates_doc, fmt)
            if rendered:
                return rendered
            # Fallback if no specific template
            formatted = format_value(value, fmt)
            label = field_meta.get(field_name, {}).get("label", field_name)
            return f"Your {label.lower()} is ₹{formatted}." if fmt == "currency" else f"Your {label.lower()} is {formatted}."

        else:
            # Multiple specific fields
            logger.debug("template_rendering_multi_field", fields=requested_fields)
            field_data = {
                fn: mapped_data.get(fn)
                for fn in requested_fields
                if mapped_data.get(fn) is not None
            }
            return self.render_multi_field(field_data, templates_doc, field_definitions)


# Singleton
template_engine = TemplateEngine()
