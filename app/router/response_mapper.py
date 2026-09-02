"""
Response Mapper
================

PURPOSE:
    Translates a raw ERP JSON response into PhinsIQ's standardized field names
    using the 'response_mapping' configuration from the api_registry.

    Raw ERP response (SJBHS):
        {
            "total_fee_amount": 85000,
            "paid_amount": 42500,
            "pending_amount": 42500,
            "instalment_amt": 21250,
            "studentInfo": {
                "student_name": "Arjun Kumar",
                "term_name": "Term 1 2026"
            }
        }

    After mapping (PhinsIQ standard):
        {
            "total_fee": 85000,
            "paid_amount": 42500,
            "pending_amount": 42500,
            "installment_amount": 21250,
            "student_name": "Arjun Kumar",
            "term": "Term 1 2026"
        }

WHY MAPPING MATTERS:
    Institution A returns: {"attendancePercentage": 94.7}
    Institution B returns: {"attendance_pct": 94.7}
    Institution C returns: {"att_per": 94.7}

    After mapping, all three produce: {"percentage": 94.7}

    The template engine and response builder only know PhinsIQ standard names.
    They don't care how each institution names their fields.

DOT NOTATION FOR NESTED FIELDS:
    The mapping config uses dot notation for nested JSON:
        "student_name": "studentInfo.student_name"
    This means: look in response["studentInfo"]["student_name"]

    This handles any depth of nesting without extra code.
"""

from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_nested_value(data: Any, dot_path: str) -> Any:
    """
    Extract a value from a nested dict or list using dot notation.

    WHY DOT NOTATION?
        ERP responses often have nested objects or arrays:
            {"studentInfo": {"student_name": "Arjun"}}
            {"attendance_data": [{"date": "2026-06-03", "status": "present"}]}

    Features:
        - Nested objects: "studentInfo.student_name" -> "Arjun"
        - Array index: "attendance_data.0.status" -> "present"
        - Array field projection: "attendance_data.status" -> ["present", "present", ...]
    """
    if not dot_path:
        return data

    keys = dot_path.split(".")
    current = data

    for i, key in enumerate(keys):
        if current is None:
            return None

        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            if key.isdigit():
                idx = int(key)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                remaining_path = ".".join(keys[i:])
                results = [get_nested_value(item, remaining_path) for item in current if isinstance(item, (dict, list))]
                results = [r for r in results if r is not None]
                return results if results else None
        else:
            return None

    return current


def format_value(value: Any, format_type: str) -> str:
    """
    Format a raw ERP value into a display-ready string.

    Args:
        value:       Raw value from ERP (int, float, str, bool, list, etc.)
        format_type: How to format it:
                       "currency"  → 85,000
                       "percentage" → 86.9%
                       "boolean"   → Enabled / Disabled
                       "list"      → item1, item2, item3 (comma-joined)
                       "date_list" → 03 Jun, 08 Jun, ... (formatted ISO dates)
                       "text"      → raw str(value)

    Returns:
        Formatted string representation
    """
    if value is None:
        return "N/A"

    if format_type == "currency":
        try:
            # Convert to float first (ERP might return strings like "15000")
            numeric = float(str(value).replace(",", ""))
            # Format with commas for Indian number system: 1,50,000
            # Using standard comma formatting for simplicity in V1
            return f"{numeric:,.0f}"
        except (ValueError, TypeError):
            return str(value)

    elif format_type == "percentage":
        try:
            numeric = float(str(value))
            return f"{numeric:.1f}%"
        except (ValueError, TypeError):
            return str(value)

    elif format_type == "boolean":
        if isinstance(value, bool):
            return "Enabled" if value else "Disabled"
        if str(value).lower() in ("1", "true", "yes"):
            return "Enabled"
        return "Disabled"

    elif format_type == "list":
        # For lists returned by ArrayAggregator (e.g., holidays, homework, notifications)
        if isinstance(value, list):
            if not value:
                return "None"
            # If items already contain newlines, join with double newline
            if any("\n" in str(v) for v in value):
                return "\n\n".join(str(v) for v in value)
            # If items are already prefixed with numbers/bullets or emojis
            if any(str(v).startswith(("•", "-", "*", "1.", "2.", "3.", "📢", "⏳", "✅", "📚", "🌴", "🏫")) for v in value):
                return "\n".join(str(v) for v in value)
            # Format each item on its own line with a bullet point
            return "\n".join(f"• {v}" for v in value)
        return str(value)

    elif format_type == "date_list":
        # Format a list of ISO date strings ("YYYY-MM-DD") into readable form
        if isinstance(value, list):
            if not value:
                return "None"
            return "\n".join(f"• {_format_iso_date(str(d))}" for d in value)
        return _format_iso_date(str(value))

    else:
        # Handle plain lists with text format as well (fallback)
        if isinstance(value, list):
            if not value:
                return "None"
            return ", ".join(str(v) for v in value)
        return str(value)


def _format_iso_date(iso_date: str) -> str:
    """
    Format an ISO date string ("YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS") into a human-readable form.

    Examples:
        "2026-06-08" → "08 Jun 2026"
        "2025-06-02 12:06:00" → "02 Jun 2025"
        "2026-08-28" → "28 Aug 2026"

    Falls back to the original string on any parsing error.
    """
    if not iso_date:
        return ""
    from datetime import datetime
    cleaned = str(iso_date).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%d %b %Y")
        except (ValueError, TypeError):
            pass
    try:
        # Fallback to first 10 characters (YYYY-MM-DD)
        if len(cleaned) >= 10 and cleaned[4] == "-" and cleaned[7] == "-":
            dt = datetime.strptime(cleaned[:10], "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
    except Exception:
        pass
    return iso_date


class ResponseMapper:
    """
    Maps raw ERP API responses to PhinsIQ's standardized field names.

    This class is stateless — it doesn't store any state between calls.
    The mapping configuration comes from the api_registry document,
    which is loaded per-request from MongoDB (cached).
    """

    def map(
        self,
        raw_response: dict,
        response_mapping: dict[str, str],
        response_root: Optional[str] = None,
        field_formats: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Apply response_mapping to extract and rename fields from the ERP response.

        Args:
            raw_response:      The full JSON response from the ERP API
            response_mapping:  Dict of {phinsiq_name: erp_field_path}
                               e.g., {"total_fee": "total_fee_amount"}
                               or    {"student_name": "studentInfo.student_name"}
            response_root:     If data is nested under a key (e.g., "data"),
                               provide that key here. None = use root.
            field_formats:     Optional dict of {field_name: format_type}
                               Used to format values for display.

        Returns:
            Dict with PhinsIQ standard field names and their values.
            Missing ERP fields have None values.

        Example:
            raw: {"total_fee_amount": 85000, "studentInfo": {"student_name": "Arjun"}}
            mapping: {"total_fee": "total_fee_amount", "student_name": "studentInfo.student_name"}
            result: {"total_fee": 85000, "student_name": "Arjun"}
        """
        # Navigate to response_root if specified
        data = raw_response
        if response_root:
            data = raw_response.get(response_root, {})
            if not isinstance(data, dict):
                logger.warning(
                    "response_root_not_dict",
                    response_root=response_root,
                    actual_type=type(data).__name__,
                )
                data = raw_response  # Fall back to root

        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]

        mapped: dict[str, Any] = {}

        for phinsiq_name, erp_path in response_mapping.items():
            value = get_nested_value(data, erp_path)
            mapped[phinsiq_name] = value

            if value is None:
                logger.debug(
                    "mapping_field_missing",
                    phinsiq_field=phinsiq_name,
                    erp_path=erp_path,
                )

        logger.debug(
            "response_mapped",
            total_fields=len(response_mapping),
            found_fields=sum(1 for v in mapped.values() if v is not None),
        )

        return mapped

    def extract_fields(
        self,
        mapped_response: dict[str, Any],
        requested_fields: list[str],
    ) -> dict[str, Any]:
        """
        Extract only the fields the user asked for from the fully mapped response.

        EXAMPLE:
            User asked for: ["pending_amount", "paid_amount"]
            Mapped response has ALL fields (total_fee, pending, paid, installment...)
            This function returns only: {"pending_amount": 42500, "paid_amount": 42500}

        WHY THIS STEP?
            The api_registry maps ALL fields we might ever need from this ERP.
            But we only return what the user asked for. This:
            1. Keeps responses focused
            2. Prevents information overload
            3. Makes template rendering simple

        Args:
            mapped_response:  The full mapped response (all fields)
            requested_fields: List of PhinsIQ field names the user wants

        Returns:
            Dict containing only the requested fields and their values.
        """
        return {
            field_name: mapped_response.get(field_name)
            for field_name in requested_fields
            if field_name in mapped_response
        }


# Singleton
response_mapper = ResponseMapper()
