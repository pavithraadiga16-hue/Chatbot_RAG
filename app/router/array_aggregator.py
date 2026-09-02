"""
Array Aggregator
=================

PURPOSE:
    Computes derived fields from ERP array responses using operation configs
    stored in MongoDB. No field names, filter values, or operations are
    hardcoded here — all come from the 'aggregation' block in each field
    definition.

WHY THIS EXISTS:
    Scalar fields (pending_amount, total_fee) are handled by ResponseMapper:
        raw["total_fee_amount"] → mapped["total_fee"] = 85000

    But array-based modules (Attendance, Transport, etc.) return lists:
        raw["attendance_data"] = [
            {"date": "2026-06-03", "status": "present"},
            {"date": "2026-06-08", "status": "absent"},
            ...
        ]

    Users ask: "How many absents?" → count items where status == "absent"
    Users ask: "Show absent dates" → list of dates where status == "absent"
    Users ask: "Attendance percentage?" → present_count / total * 100

    ResponseMapper cannot compute these — it only extracts values.
    ArrayAggregator computes derived values FROM the raw array.

DATABASE-DRIVEN DESIGN:
    Institution A (SJBHS):
        attendance array key: "attendance_data"
        status key: "status"
        present value: "present"
        absent value: "absent"
        date key: "date"

    Institution B (some other school):
        attendance array key: "att_records"
        status key: "att_status"
        present value: "P"
        absent value: "A"
        date key: "att_date"

    The SAME aggregator code handles BOTH — because the config in MongoDB
    tells it what keys and values to look for. Zero code changes needed.

SUPPORTED OPERATIONS:
    count           → total number of items in the array
    count_where     → count of items matching a filter condition
    filter_dates    → list of date values from items matching a condition
    filter_values   → list of any field values from items matching a condition
    percentage      → (count_where / total) * 100
    max_date        → latest date string from filtered items
    min_date        → earliest date string from filtered items

AGGREGATION CONFIG SCHEMA (in MongoDB 'fields' collection):
    {
      "name": "absent_count",
      "aggregation": {
        "source_field": "attendance_data",   // dot-path into raw ERP response
        "operation": "count_where",
        "filter_key": "status",              // key inside each array item
        "filter_value": "absent"             // value to match
      }
    }

    {
      "name": "absent_dates",
      "aggregation": {
        "source_field": "attendance_data",
        "operation": "filter_dates",
        "filter_key": "status",
        "filter_value": "absent",
        "date_key": "date"                   // which key holds the date
      }
    }

    {
      "name": "attendance_percentage",
      "aggregation": {
        "source_field": "attendance_data",
        "operation": "percentage",
        "filter_key": "status",
        "filter_value": "present"
      }
    }
"""

from typing import Any, Optional
from app.core.logging import get_logger
from app.router.response_mapper import get_nested_value

logger = get_logger(__name__)


class ArrayAggregator:
    """
    Computes derived values from ERP array fields using DB-configured operations.

    This class is stateless — it takes raw ERP data and field definitions,
    and returns a dict of computed {phinsiq_field_name: computed_value}.

    It is called AFTER ResponseMapper so that scalar fields are already
    mapped. The aggregator enriches mapped_data with computed fields.
    """

    def aggregate(
        self,
        raw_response: dict,
        field_definitions: list[dict],
        response_root: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run all aggregation operations for fields that have an 'aggregation' config.

        Args:
            raw_response:      The full raw JSON response from the ERP API.
            field_definitions: List of field dicts from MongoDB 'fields' collection.
                               Only fields with an 'aggregation' block are processed.
            response_root:     Optional key to navigate into before reading arrays.
            query_text:        Optional user message text for dynamic search operations.

        Returns:
            Dict of {phinsiq_field_name: computed_value} for all aggregatable fields.
            Non-aggregatable fields are skipped (handled by ResponseMapper).
        """
        # Navigate to response_root if specified
        data = raw_response
        if response_root:
            rooted = raw_response.get(response_root)
            if isinstance(rooted, dict):
                data = rooted

        computed: dict[str, Any] = {}

        for field_def in field_definitions:
            agg_config = field_def.get("aggregation")
            if not agg_config:
                continue  # Scalar field — handled by ResponseMapper

            field_name = field_def.get("name", "")
            if not field_name:
                continue

            try:
                result = self._run_operation(data, agg_config, query_text=query_text)
                computed[field_name] = result
                logger.debug(
                    "array_aggregation_success",
                    field=field_name,
                    operation=agg_config.get("operation"),
                    result_preview=str(result)[:80],
                )
            except Exception as e:
                logger.warning(
                    "array_aggregation_failed",
                    field=field_name,
                    operation=agg_config.get("operation"),
                    error=str(e),
                )
                computed[field_name] = None

        return computed

    def _run_operation(self, data: dict, agg_config: dict, query_text: Optional[str] = None) -> Any:
        """
        Dispatch to the correct operation handler based on agg_config['operation'].

        Args:
            data:       The ERP response data (possibly rooted)
            agg_config: The aggregation config dict from the field definition

        Returns:
            The computed value — int, float, list[str], or str depending on op.
        """
        operation = agg_config.get("operation", "")
        source_field = agg_config.get("source_field", "")

        # Resolve the source array using dot notation (e.g., "data.attendance_data")
        source_array = get_nested_value(data, source_field)

        if source_array is None:
            logger.debug("array_source_not_found", source_field=source_field)
            return None

        if not isinstance(source_array, list):
            logger.warning(
                "array_source_not_a_list",
                source_field=source_field,
                actual_type=type(source_array).__name__,
            )
            return None

        if operation == "count":
            return self._op_count(source_array)

        elif operation == "count_where":
            filter_key = agg_config.get("filter_key", "")
            filter_value = agg_config.get("filter_value", "")
            return self._op_count_where(source_array, filter_key, filter_value)

        elif operation == "filter_dates":
            filter_key = agg_config.get("filter_key", "")
            filter_value = agg_config.get("filter_value", "")
            date_key = agg_config.get("date_key", "date")
            return self._op_filter_dates(source_array, filter_key, filter_value, date_key)

        elif operation == "filter_values":
            filter_key = agg_config.get("filter_key", "")
            filter_value = agg_config.get("filter_value", "")
            value_key = agg_config.get("value_key", "")
            return self._op_filter_values(source_array, filter_key, filter_value, value_key)

        elif operation == "percentage":
            filter_key = agg_config.get("filter_key", "")
            filter_value = agg_config.get("filter_value", "")
            decimal_places = agg_config.get("decimal_places", 1)
            return self._op_percentage(source_array, filter_key, filter_value, decimal_places)

        elif operation == "max_date":
            filter_key = agg_config.get("filter_key")
            filter_value = agg_config.get("filter_value")
            date_key = agg_config.get("date_key", "date")
            return self._op_max_date(source_array, filter_key, filter_value, date_key)

        elif operation == "min_date":
            filter_key = agg_config.get("filter_key")
            filter_value = agg_config.get("filter_value")
            date_key = agg_config.get("date_key", "date")
            return self._op_min_date(source_array, filter_key, filter_value, date_key)

        elif operation == "filter_events_contains":
            search_key = agg_config.get("search_key", "title")
            contains_value = agg_config.get("contains_value", "")
            title_key = agg_config.get("title_key", "title")
            start_key = agg_config.get("start_key", "start")
            end_key = agg_config.get("end_key", "end")
            return self._op_filter_events_contains(source_array, search_key, contains_value, title_key, start_key, end_key)

        elif operation == "count_where_contains":
            search_key = agg_config.get("search_key", "title")
            contains_value = agg_config.get("contains_value", "")
            return self._op_count_where_contains(source_array, search_key, contains_value)

        elif operation == "calculate_event_duration":
            match_title = agg_config.get("match_title", "")
            title_key = agg_config.get("title_key", "title")
            start_key = agg_config.get("start_key", "start")
            end_key = agg_config.get("end_key", "end")
            return self._op_calculate_event_duration(source_array, match_title, title_key, start_key, end_key)

        elif operation in ("search_event_title", "dynamic_event_search"):
            search_query = agg_config.get("search_query") or query_text or ""
            title_key = agg_config.get("title_key", "title")
            start_key = agg_config.get("start_key", "start")
            end_key = agg_config.get("end_key", "end")
            return self._op_search_event_title(source_array, search_query, title_key, start_key, end_key)

        elif operation == "count_where_not":
            filter_key = agg_config.get("filter_key", "status")
            filter_value = agg_config.get("filter_value", "completed")
            return self._op_count_where_not(source_array, filter_key, filter_value)

        elif operation == "filter_homework_list":
            filter_key = agg_config.get("filter_key")
            filter_value = agg_config.get("filter_value")
            filter_mode = agg_config.get("filter_mode", "all")
            subject_key = agg_config.get("subject_key", "subject")
            desc_key = agg_config.get("desc_key", "homework_discription")
            due_key = agg_config.get("due_key", "submission_date")
            teacher_key = agg_config.get("teacher_key", "sent_by")
            status_key = agg_config.get("status_key", "status")
            return self._op_filter_homework_list(
                source_array, filter_key, filter_value, filter_mode,
                subject_key, desc_key, due_key, teacher_key, status_key
            )

        elif operation in ("search_homework", "dynamic_homework_search"):
            search_query = agg_config.get("search_query") or query_text or ""
            subject_key = agg_config.get("subject_key", "subject")
            desc_key = agg_config.get("desc_key", "homework_discription")
            due_key = agg_config.get("due_key", "submission_date")
            teacher_key = agg_config.get("teacher_key", "sent_by")
            status_key = agg_config.get("status_key", "status")
            return self._op_dynamic_homework_search(
                source_array, search_query,
                subject_key, desc_key, due_key, teacher_key, status_key
            )

        elif operation == "filter_recent_notifications":
            limit = agg_config.get("limit", 3)
            title_key = agg_config.get("title_key", "subject")
            desc_key = agg_config.get("desc_key", "message")
            date_key = agg_config.get("date_key", "date_time")
            sender_key = agg_config.get("sender_key", "sent_by")
            type_key = agg_config.get("type_key", "type")
            return self._op_filter_recent_notifications(
                source_array, limit, title_key, desc_key, date_key, sender_key, type_key
            )

        elif operation == "filter_notifications_list":
            title_key = agg_config.get("title_key", "subject")
            desc_key = agg_config.get("desc_key", "message")
            date_key = agg_config.get("date_key", "date_time")
            sender_key = agg_config.get("sender_key", "sent_by")
            type_key = agg_config.get("type_key", "type")
            return self._op_filter_notifications_list(
                source_array, title_key, desc_key, date_key, sender_key, type_key
            )

        elif operation in ("search_notification", "dynamic_notification_search"):
            search_query = agg_config.get("search_query") or query_text or ""
            title_key = agg_config.get("title_key", "subject")
            desc_key = agg_config.get("desc_key", "message")
            date_key = agg_config.get("date_key", "date_time")
            sender_key = agg_config.get("sender_key", "sent_by")
            type_key = agg_config.get("type_key", "type")
            return self._op_dynamic_notification_search(
                source_array, search_query,
                title_key, desc_key, date_key, sender_key, type_key
            )

        elif operation == "filter_recent_study_materials":
            limit = agg_config.get("limit", 3)
            subject_key = agg_config.get("subject_key", "subject_name")
            type_key = agg_config.get("type_key", "type")
            desc_key = agg_config.get("desc_key", "description")
            doc_key = agg_config.get("doc_key", "document_name_url")
            date_key = agg_config.get("date_key", "created_date_time")
            teacher_key = agg_config.get("teacher_key", "name")
            return self._op_filter_recent_study_materials(
                source_array, limit, subject_key, type_key, desc_key, doc_key, date_key, teacher_key
            )

        elif operation == "filter_study_materials_list":
            subject_key = agg_config.get("subject_key", "subject_name")
            type_key = agg_config.get("type_key", "type")
            desc_key = agg_config.get("desc_key", "description")
            doc_key = agg_config.get("doc_key", "document_name_url")
            date_key = agg_config.get("date_key", "created_date_time")
            teacher_key = agg_config.get("teacher_key", "name")
            return self._op_filter_study_materials_list(
                source_array, subject_key, type_key, desc_key, doc_key, date_key, teacher_key
            )

        elif operation in ("search_study_materials", "dynamic_study_material_search"):
            search_query = agg_config.get("search_query") or query_text or ""
            subject_key = agg_config.get("subject_key", "subject_name")
            type_key = agg_config.get("type_key", "type")
            desc_key = agg_config.get("desc_key", "description")
            doc_key = agg_config.get("doc_key", "document_name_url")
            date_key = agg_config.get("date_key", "created_date_time")
            teacher_key = agg_config.get("teacher_key", "name")
            return self._op_dynamic_study_material_search(
                source_array, search_query,
                subject_key, type_key, desc_key, doc_key, date_key, teacher_key
            )

        else:
            logger.warning("array_unknown_operation", operation=operation)
            return None

    # ------------------------------------------------------------------
    # Operation Implementations
    # ------------------------------------------------------------------

    def _op_count(self, source_array: list) -> int:
        """
        Count total items in the array.
        Example: total number of school days recorded.
        """
        return len(source_array)

    def _op_count_where(
        self,
        source_array: list,
        filter_key: str,
        filter_value: str,
    ) -> int:
        """
        Count items where item[filter_key] == filter_value.
        Example: count absences → items where status == "absent"

        Case-insensitive comparison for robustness.
        """
        count = 0
        filter_val_lower = str(filter_value).lower()
        for item in source_array:
            if not isinstance(item, dict):
                continue
            item_val = str(item.get(filter_key, "")).lower()
            if item_val == filter_val_lower:
                count += 1
        return count

    def _op_filter_dates(
        self,
        source_array: list,
        filter_key: str,
        filter_value: str,
        date_key: str,
    ) -> list[str]:
        """
        Return list of date values from items matching the filter.
        Example: absent dates → dates where status == "absent"

        Returns ISO date strings (e.g., "2026-06-08").
        Sorted chronologically.
        """
        dates = []
        filter_val_lower = str(filter_value).lower()
        for item in source_array:
            if not isinstance(item, dict):
                continue
            item_val = str(item.get(filter_key, "")).lower()
            if item_val == filter_val_lower:
                date = item.get(date_key)
                if date:
                    dates.append(str(date))
        return sorted(dates)

    def _op_filter_values(
        self,
        source_array: list,
        filter_key: str,
        filter_value: str,
        value_key: str,
    ) -> list[Any]:
        """
        Return a list of any field's values from filtered items.
        More generic than filter_dates — works for any field.
        Example: list of IDs of absent records.
        """
        values = []
        filter_val_lower = str(filter_value).lower()
        for item in source_array:
            if not isinstance(item, dict):
                continue
            item_val = str(item.get(filter_key, "")).lower()
            if item_val == filter_val_lower:
                val = item.get(value_key)
                if val is not None:
                    values.append(val)
        return values

    def _op_percentage(
        self,
        source_array: list,
        filter_key: str,
        filter_value: str,
        decimal_places: int = 1,
    ) -> Optional[float]:
        """
        Compute (count_where / total) * 100.
        Example: attendance % → (present_count / total_days) * 100

        Returns None if array is empty (avoid division by zero).
        """
        total = len(source_array)
        if total == 0:
            return None
        matching = self._op_count_where(source_array, filter_key, filter_value)
        pct = (matching / total) * 100
        return round(pct, decimal_places)

    def _op_max_date(
        self,
        source_array: list,
        filter_key: Optional[str],
        filter_value: Optional[str],
        date_key: str,
    ) -> Optional[str]:
        """
        Return the maximum (latest) date from the array, optionally filtered.
        Example: last present date → max date where status == "present"

        Works because ISO date strings ("YYYY-MM-DD") sort lexicographically.
        """
        dates = self._collect_dates(source_array, filter_key, filter_value, date_key)
        return max(dates) if dates else None

    def _op_min_date(
        self,
        source_array: list,
        filter_key: Optional[str],
        filter_value: Optional[str],
        date_key: str,
    ) -> Optional[str]:
        """
        Return the minimum (earliest) date from the array, optionally filtered.
        Example: first absent date → min date where status == "absent"
        """
        dates = self._collect_dates(source_array, filter_key, filter_value, date_key)
        return min(dates) if dates else None

    def _collect_dates(
        self,
        source_array: list,
        filter_key: Optional[str],
        filter_value: Optional[str],
        date_key: str,
    ) -> list[str]:
        """
        Helper: collect date strings from array items, with optional filter.
        """
        dates = []
        filter_val_lower = str(filter_value).lower() if filter_value else None

        for item in source_array:
            if not isinstance(item, dict):
                continue
            # Apply filter if specified
            if filter_key and filter_val_lower is not None:
                item_val = str(item.get(filter_key, "")).lower()
                if item_val != filter_val_lower:
                    continue
            date = item.get(date_key)
            if date:
                dates.append(str(date))
        return dates

    def _op_filter_events_contains(
        self,
        source_array: list,
        search_key: str,
        contains_value: str,
        title_key: str = "title",
        start_key: str = "start",
        end_key: str = "end",
    ) -> list[str]:
        """
        Extracts events where item[search_key] contains `contains_value`.
        Formats each event as: 'Event Title — Date (or Date to Date)'.
        """
        from app.router.response_mapper import _format_iso_date
        results = []
        match_str = str(contains_value).lower().strip()

        for item in source_array:
            if not isinstance(item, dict):
                continue
            val = str(item.get(search_key, "")).lower()
            # If contains_value is empty, match all items
            if not match_str or match_str in val:
                raw_title = " ".join(str(item.get(title_key, "")).split())
                if not raw_title:
                    continue

                raw_start = item.get(start_key)
                raw_end = item.get(end_key)

                start_formatted = _format_iso_date(str(raw_start)) if raw_start else ""
                end_formatted = _format_iso_date(str(raw_end)) if raw_end else ""

                # If single-day event or start and end formatted date are identical
                if not end_formatted or start_formatted == end_formatted:
                    date_display = start_formatted or "Date TBA"
                else:
                    date_display = f"{start_formatted} to {end_formatted}"

                results.append(f"{raw_title} — {date_display}")

        return results

    def _op_count_where_contains(
        self,
        source_array: list,
        search_key: str,
        contains_value: str,
    ) -> int:
        """
        Count items where item[search_key] contains `contains_value`.
        Example: count how many items have '(Holiday)' in title.
        """
        match_str = str(contains_value).lower().strip()
        count = 0
        for item in source_array:
            if not isinstance(item, dict):
                continue
            val = str(item.get(search_key, "")).lower()
            if match_str in val:
                count += 1
        return count

    def _op_calculate_event_duration(
        self,
        source_array: list,
        match_title: str,
        title_key: str = "title",
        start_key: str = "start",
        end_key: str = "end",
    ) -> Optional[str]:
        """
        Calculates duration in days for an event by title difference: (end - start) + 1 day.
        """
        from datetime import datetime
        from app.router.response_mapper import _format_iso_date

        def _parse_dt(d_val: Any) -> Optional[datetime]:
            if not d_val:
                return None
            s = str(d_val).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            try:
                if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                    return datetime.strptime(s[:10], "%Y-%m-%d")
            except Exception:
                pass
            return None

        match_str = str(match_title).lower().strip()
        for item in source_array:
            if not isinstance(item, dict):
                continue
            title = str(item.get(title_key, "")).strip()
            if match_str in title.lower():
                s_dt = _parse_dt(item.get(start_key))
                e_dt = _parse_dt(item.get(end_key))
                if s_dt and e_dt:
                    days = (e_dt.date() - s_dt.date()).days + 1
                    s_fmt = _format_iso_date(str(item.get(start_key)))
                    e_fmt = _format_iso_date(str(item.get(end_key)))
                    if days > 1:
                        return f"{title} is scheduled for {days} days ({s_fmt} to {e_fmt})"
                    else:
                        return f"{title} is a 1-day event on {s_fmt}"
        return None

    def _op_search_event_title(
        self,
        source_array: list,
        search_query: str,
        title_key: str = "title",
        start_key: str = "start",
        end_key: str = "end",
    ) -> Optional[str]:
        """
        Searches for an event by query words OR exact date, returning its title, dates, and duration.
        Supports queries like:
        - "what is there on 20 Oct 2025?"
        - "what is there on 20 october 2025"
        - "what is there on 20/09/2025" or "20-09-2025" or "2025-10-20"
        - "When is Final Assessment Commences PKG to Std 9?"
        - "When is MERAKI?"
        """
        import re
        from datetime import datetime, date
        from app.router.response_mapper import _format_iso_date

        if not search_query or not source_array:
            return None

        def _parse_dt(d_val: Any) -> Optional[datetime]:
            if not d_val:
                return None
            s = str(d_val).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            try:
                if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                    return datetime.strptime(s[:10], "%Y-%m-%d")
            except Exception:
                pass
            return None

        MONTHS_MAP = {
            "jan": 1, "january": 1,
            "feb": 2, "february": 2,
            "mar": 3, "march": 3,
            "apr": 4, "april": 4,
            "may": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7,
            "aug": 8, "august": 8,
            "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12,
        }

        def _extract_date_from_text(q_str: str) -> Optional[datetime]:
            q_lower = q_str.lower().strip()

            # 1. Matches: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD/MM/YY, DD-MM-YY
            m1 = re.search(r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b', q_lower)
            if m1:
                d, m_num, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
                if y < 100:
                    y += 2000
                try:
                    return datetime(y, m_num, d)
                except ValueError:
                    pass

            # 2. Matches: YYYY-MM-DD, YYYY/MM/DD
            m2 = re.search(r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b', q_lower)
            if m2:
                y, m_num, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
                try:
                    return datetime(y, m_num, d)
                except ValueError:
                    pass

            # 3. Matches: 20th Oct 2025, 20 Oct 2025, 20 October 2025, 20-Oct-2025, 20th October
            m3 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?[\s\-]+([a-z]+)(?:[\s\-]+(\d{2,4}))?\b', q_lower)
            if m3:
                d = int(m3.group(1))
                m_name = m3.group(2).lower()
                y_str = m3.group(3)
                if m_name in MONTHS_MAP:
                    m_num = MONTHS_MAP[m_name]
                    y = int(y_str) if y_str else (2025 if m_num >= 6 else 2026)
                    if y < 100:
                        y += 2000
                    try:
                        return datetime(y, m_num, d)
                    except ValueError:
                        pass

            # 4. Matches: Oct 20 2025, October 20th 2025, October 20, 2025
            m4 = re.search(r'\b([a-z]+)[\s\-]+(\d{1,2})(?:st|nd|rd|th)?(?:,?[\s\-]+(\d{2,4}))?\b', q_lower)
            if m4:
                m_name = m4.group(1).lower()
                d = int(m4.group(2))
                y_str = m4.group(3)
                if m_name in MONTHS_MAP:
                    m_num = MONTHS_MAP[m_name]
                    y = int(y_str) if y_str else (2025 if m_num >= 6 else 2026)
                    if y < 100:
                        y += 2000
                    try:
                        return datetime(y, m_num, d)
                    except ValueError:
                        pass

            return None

        # ------------------------------------------------------------------
        # PATH A: Date-Based Calendar Search (e.g. "what is on 20 Oct 2025?")
        # ------------------------------------------------------------------
        target_dt = _extract_date_from_text(search_query)
        if target_dt:
            target_date = target_dt.date()
            formatted_target = target_dt.strftime("%d %b %Y")

            matching_date_events = []
            for item in source_array:
                if not isinstance(item, dict):
                    continue
                raw_title = " ".join(str(item.get(title_key, "")).split())
                if not raw_title:
                    continue

                s_dt = _parse_dt(item.get(start_key))
                e_dt = _parse_dt(item.get(end_key))

                if s_dt and e_dt:
                    if s_dt.date() <= target_date <= e_dt.date():
                        matching_date_events.append((item, raw_title, s_dt, e_dt))
                elif s_dt:
                    if s_dt.date() == target_date:
                        matching_date_events.append((item, raw_title, s_dt, s_dt))

            if not matching_date_events:
                if "holiday" in search_query.lower():
                    return f"There is no holiday scheduled on **{formatted_target}** in the academic calendar."
                return f"There are no events scheduled on **{formatted_target}** in the academic calendar."

            if len(matching_date_events) == 1:
                item, title, s_dt, e_dt = matching_date_events[0]
                s_fmt = _format_iso_date(str(item.get(start_key)))
                e_fmt = _format_iso_date(str(item.get(end_key)))
                if s_dt.date() != e_dt.date():
                    days = (e_dt.date() - s_dt.date()).days + 1
                    return f"On **{formatted_target}**, **{title}** is scheduled (from **{s_fmt}** to **{e_fmt}**, {days} days)."
                else:
                    return f"On **{formatted_target}**, the scheduled event is **{title}**."
            else:
                lines = [f"📅 **Events on {formatted_target}:**\n"]
                for i, (item, title, s_dt, e_dt) in enumerate(matching_date_events, 1):
                    s_fmt = _format_iso_date(str(item.get(start_key)))
                    e_fmt = _format_iso_date(str(item.get(end_key)))
                    if s_dt.date() != e_dt.date():
                        days = (e_dt.date() - s_dt.date()).days + 1
                        lines.append(f"{i}. **{title}** — {s_fmt} to {e_fmt} ({days} days)")
                    else:
                        lines.append(f"{i}. **{title}** — {s_fmt}")
                return "\n".join(lines)

        # ------------------------------------------------------------------
        # PATH B: Keyword/Phrase Title Search (e.g. "When is Final Assessment?")
        # ------------------------------------------------------------------
        STOPWORDS = {
            "what", "when", "is", "the", "are", "on", "in", "at", "for", "held",
            "date", "dates", "timing", "schedule", "start", "starts", "will",
            "does", "do", "we", "have", "tell", "me", "show", "details", "about",
            "day", "of", "to", "please", "can", "you", "my", "our", "school",
            "happening", "scheduled"
        }

        cleaned_query = re.sub(r"[^\w\s]", " ", search_query.lower())
        query_words = [w for w in cleaned_query.split() if w not in STOPWORDS and len(w) > 1]

        if not query_words:
            query_words = [w for w in cleaned_query.split() if len(w) > 2]

        if not query_words:
            return None

        scored_items = []
        raw_query_str = " ".join(query_words)

        for item in source_array:
            if not isinstance(item, dict):
                continue
            raw_title = " ".join(str(item.get(title_key, "")).split())
            if not raw_title:
                continue

            lower_title = raw_title.lower()
            clean_title_words = set(re.sub(r"[^\w\s]", " ", lower_title).split())

            score = 0
            # 1. Exact phrase match
            if raw_query_str in lower_title:
                score += 50 + len(raw_query_str)

            # 2. Individual word matches
            matching_words = [w for w in query_words if w in clean_title_words or (len(w) >= 4 and w in lower_title)]
            score += len(matching_words) * 10

            # 3. Standard/grade specifics boost
            for q_w in query_words:
                if q_w in ("pkg", "lkg", "ukg", "11", "12", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10") and q_w in clean_title_words:
                    score += 15

            if score > 0 and matching_words:
                scored_items.append((score, item, raw_title))

        if not scored_items:
            return None

        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_score = scored_items[0][0]

        top_matches = [x for x in scored_items if x[0] >= max(top_score * 0.85, 20)]

        if len(top_matches) == 1 or (len(top_matches) > 1 and top_matches[0][0] >= top_matches[1][0] * 1.5):
            best_item = top_matches[0][1]
            title = top_matches[0][2]
            s_raw = best_item.get(start_key)
            e_raw = best_item.get(end_key)
            s_dt = _parse_dt(s_raw)
            e_dt = _parse_dt(e_raw)
            s_fmt = _format_iso_date(str(s_raw))
            e_fmt = _format_iso_date(str(e_raw))

            if s_dt and e_dt and s_dt.date() != e_dt.date():
                days = (e_dt.date() - s_dt.date()).days + 1
                return f"**{title}** is scheduled for **{days} days**, from **{s_fmt}** to **{e_fmt}**."
            else:
                return f"**{title}** is scheduled on **{s_fmt}**."

        else:
            # Multiple matches
            lines = ["Here are the matching calendar events:\n"]
            for i, (_, item, title) in enumerate(top_matches[:8], 1):
                s_raw = item.get(start_key)
                e_raw = item.get(end_key)
                s_dt = _parse_dt(s_raw)
                e_dt = _parse_dt(e_raw)
                s_fmt = _format_iso_date(str(s_raw))
                e_fmt = _format_iso_date(str(e_raw))

                if s_dt and e_dt and s_dt.date() != e_dt.date():
                    days = (e_dt.date() - s_dt.date()).days + 1
                    lines.append(f"{i}. **{title}** — {s_fmt} to {e_fmt} ({days} days)")
                else:
                    lines.append(f"{i}. **{title}** — {s_fmt}")
            return "\n".join(lines)

    def _op_count_where_not(
        self,
        source_array: list,
        filter_key: str = "status",
        filter_value: str = "completed",
    ) -> int:
        """
        Count items where item[filter_key] is NOT equal to filter_value.
        Supports comma-separated excluded values (e.g. "completed,1,submitted").
        """
        count = 0
        exclude_values = {v.strip().lower() for v in str(filter_value).split(",")}
        for item in source_array:
            if not isinstance(item, dict):
                continue
            val = str(item.get(filter_key, "")).strip().lower()
            if val not in exclude_values:
                count += 1
        return count

    def _op_filter_homework_list(
        self,
        source_array: list,
        filter_key: Optional[str] = None,
        filter_value: Optional[str] = None,
        filter_mode: str = "all",
        subject_key: str = "subject",
        desc_key: str = "homework_discription",
        due_key: str = "submission_date",
        teacher_key: str = "sent_by",
        status_key: str = "status",
    ) -> list[str]:
        """
        Filter and format homework items into clean human-readable list entries.
        """
        from app.router.response_mapper import _format_iso_date

        results = []
        target_values = {v.strip().lower() for v in str(filter_value).split(",")} if filter_value else set()

        for item in source_array:
            if not isinstance(item, dict):
                continue

            if filter_key:
                val = str(item.get(filter_key, "")).strip().lower()
                if filter_mode == "not_equals" and val in target_values:
                    continue
                elif filter_mode == "equals" and val not in target_values:
                    continue

            subj = item.get(subject_key, "").strip() or "General"
            desc = item.get(desc_key, "").strip()
            due_raw = item.get(due_key, "")
            due_fmt = _format_iso_date(str(due_raw)) if due_raw else "N/A"
            teacher = item.get(teacher_key, "").strip()
            raw_status = str(item.get(status_key, "")).strip().lower()
            status_label = "✅ Completed" if raw_status in ("completed", "1", "submitted") else "⏳ Pending"

            entry = f"📚 **{subj}**"
            if teacher:
                entry += f" (*{teacher}*)"
            if desc:
                entry += f"\n   📝 {desc}"
            entry += f"\n   📅 Due Date: **{due_fmt}** | Status: **{status_label}**"

            results.append(entry)

        return results

    def _op_dynamic_homework_search(
        self,
        source_array: list,
        search_query: str,
        subject_key: str = "subject",
        desc_key: str = "homework_discription",
        due_key: str = "submission_date",
        teacher_key: str = "sent_by",
        status_key: str = "status",
    ) -> Optional[str]:
        """
        Dynamically search homework by subject name, submission date, or teacher name.
        """
        import re
        from datetime import datetime
        from app.router.response_mapper import _format_iso_date

        if not search_query or not source_array:
            return None

        q_lower = search_query.lower().strip()

        HW_STOPWORDS = {
            "when", "what", "is", "the", "are", "on", "in", "at", "for", "held",
            "date", "dates", "timing", "schedule", "start", "starts", "will",
            "does", "do", "we", "have", "tell", "me", "show", "details", "about",
            "day", "of", "to", "please", "can", "you", "my", "our", "school",
            "homework", "homeworks", "home", "work", "assignment", "assignments",
            "submission", "submit", "due", "deadline", "pending", "completed", "give", "list"
        }

        # -------------------------------------------------------------
        # 1. Subject-specific search (e.g. "math homework", "science assignment")
        # -------------------------------------------------------------
        cleaned_words = [w for w in re.sub(r"[^\w\s]", " ", q_lower).split() if w not in HW_STOPWORDS and len(w) >= 3]
        matched_by_subject = []
        for item in source_array:
            if not isinstance(item, dict):
                continue
            subj = str(item.get(subject_key, "")).strip().lower()
            if not subj:
                continue
            # Match if subject name is mentioned or cleaned subject keyword matches
            subj_words = set(re.sub(r"[^\w\s]", " ", subj).split())
            if subj in q_lower or any(w in subj_words or (len(w) >= 4 and w in subj) for w in cleaned_words):
                matched_by_subject.append(item)

        if matched_by_subject:
            lines = [f"📖 **Homework for {matched_by_subject[0].get(subject_key, 'Subject')}:**\n"]
            for i, itm in enumerate(matched_by_subject, 1):
                subj = itm.get(subject_key, "").strip()
                desc = itm.get(desc_key, "").strip()
                due_fmt = _format_iso_date(str(itm.get(due_key, "")))
                teacher = itm.get(teacher_key, "").strip()
                raw_st = str(itm.get(status_key, "")).strip().lower()
                st_label = "✅ Completed" if raw_st in ("completed", "1", "submitted") else "⏳ Pending"

                entry = f"{i}. **{subj}**"
                if teacher:
                    entry += f" (*{teacher}*)"
                if desc:
                    entry += f"\n   📝 {desc}"
                entry += f"\n   📅 Due: **{due_fmt}** | Status: **{st_label}**"
                lines.append(entry)
            return "\n".join(lines)

        # -------------------------------------------------------------
        # 2. Due Date / Submission Deadline Queries (e.g. "when is submission date", "homework due")
        # -------------------------------------------------------------
        if any(kw in q_lower for kw in ("submission", "submit", "due date", "deadline", "when to submit")):
            # Sort pending/all homework by submission date
            valid_items = [itm for itm in source_array if isinstance(itm, dict) and itm.get(due_key)]
            if valid_items:
                valid_items.sort(key=lambda x: str(x.get(due_key, "")))
                lines = ["📅 **Upcoming Homework Submission Deadlines:**\n"]
                for i, itm in enumerate(valid_items[:6], 1):
                    subj = itm.get(subject_key, "").strip()
                    desc = itm.get(desc_key, "").strip()
                    due_fmt = _format_iso_date(str(itm.get(due_key, "")))
                    raw_st = str(itm.get(status_key, "")).strip().lower()
                    st_label = "✅ Completed" if raw_st in ("completed", "1", "submitted") else "⏳ Pending"

                    entry = f"{i}. **{subj}** — Due: **{due_fmt}** ({st_label})"
                    if desc:
                        entry += f"\n   📝 {desc}"
                    lines.append(entry)
                return "\n".join(lines)

        # -------------------------------------------------------------
        # 3. Pending Homework Quick Query (e.g. "pending", "incomplete")
        # -------------------------------------------------------------
        if any(kw in q_lower for kw in ("pending", "not completed", "incomplete", "left", "to do")):
            pending_items = [
                itm for itm in source_array
                if isinstance(itm, dict) and str(itm.get(status_key, "")).strip().lower() not in ("completed", "1", "submitted")
            ]
            if not pending_items:
                return "🎉 You have no pending homework! All assignments are completed."

            lines = [f"⏳ **You have {len(pending_items)} pending homework assignment(s):**\n"]
            for i, itm in enumerate(pending_items, 1):
                subj = itm.get(subject_key, "").strip()
                desc = itm.get(desc_key, "").strip()
                due_fmt = _format_iso_date(str(itm.get(due_key, "")))
                teacher = itm.get(teacher_key, "").strip()

                entry = f"{i}. **{subj}**"
                if teacher:
                    entry += f" (*{teacher}*)"
                if desc:
                    entry += f"\n   📝 {desc}"
                entry += f"\n   📅 Due: **{due_fmt}**"
                lines.append(entry)
            return "\n".join(lines)

        return None

    def _op_filter_recent_notifications(
        self,
        source_array: list,
        limit: int = 3,
        title_key: str = "subject",
        desc_key: str = "message",
        date_key: str = "date_time",
        sender_key: str = "sent_by",
        type_key: str = "type",
    ) -> list[str]:
        """
        Sort notifications by date_time descending and format the top `limit` recent items.
        """
        from datetime import datetime
        from app.router.response_mapper import _format_iso_date

        def _parse_dt(d_val: Any) -> datetime:
            if not d_val:
                return datetime.min
            s = str(d_val).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            return datetime.min

        valid_items = [itm for itm in source_array if isinstance(itm, dict)]
        if not valid_items:
            return []

        sorted_items = sorted(valid_items, key=lambda x: _parse_dt(x.get(date_key)), reverse=True)

        results = []
        for itm in sorted_items[:limit]:
            title = str(itm.get(title_key, "")).strip() or "Announcement"
            desc = str(itm.get(desc_key, "")).strip()
            sender = str(itm.get(sender_key, "")).strip()
            dt_raw = str(itm.get(date_key, ""))
            dt_fmt = _format_iso_date(dt_raw) if dt_raw else "N/A"

            entry = f"📢 **{title}**"
            if sender:
                entry += f" (*{sender}*)"
            entry += f"\n   🕒 Date: **{dt_fmt}**"
            if desc:
                entry += f"\n   📝 {desc}"

            results.append(entry)

        return results

    def _op_filter_notifications_list(
        self,
        source_array: list,
        title_key: str = "subject",
        desc_key: str = "message",
        date_key: str = "date_time",
        sender_key: str = "sent_by",
        type_key: str = "type",
    ) -> list[str]:
        """
        Format all notifications sorted by date_time descending.
        """
        return self._op_filter_recent_notifications(
            source_array,
            limit=len(source_array),
            title_key=title_key,
            desc_key=desc_key,
            date_key=date_key,
            sender_key=sender_key,
            type_key=type_key,
        )

    def _op_dynamic_notification_search(
        self,
        source_array: list,
        search_query: str,
        title_key: str = "subject",
        desc_key: str = "message",
        date_key: str = "date_time",
        sender_key: str = "sent_by",
        type_key: str = "type",
    ) -> Optional[str]:
        """
        Dynamically search notifications by exact/natural date, subject keyword, sender, or recent notice query.
        """
        import re
        from datetime import datetime
        from app.router.response_mapper import _format_iso_date

        if not search_query or not source_array:
            return None

        q_lower = search_query.lower().strip()

        def _parse_dt(d_val: Any) -> Optional[datetime]:
            if not d_val:
                return None
            s = str(d_val).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            return None

        MONTHS_MAP = {
            "jan": 1, "january": 1, "feb": 2, "february": 2,
            "mar": 3, "march": 3, "apr": 4, "april": 4,
            "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
            "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
        }

        def _extract_date_from_text(q_str: str) -> Optional[datetime]:
            ql = q_str.lower().strip()
            # 1. DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
            m1 = re.search(r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b', ql)
            if m1:
                d, m_num, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
                if y < 100:
                    y += 2000
                try:
                    return datetime(y, m_num, d)
                except ValueError:
                    pass

            # 2. YYYY-MM-DD
            m2 = re.search(r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b', ql)
            if m2:
                y, m_num, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
                try:
                    return datetime(y, m_num, d)
                except ValueError:
                    pass

            # 3. 20th Oct 2025, 20 October 2025, 20 October
            m3 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?[\s\-]+([a-z]+)(?:[\s\-]+(\d{2,4}))?\b', ql)
            if m3:
                d = int(m3.group(1))
                m_name = m3.group(2).lower()
                y_str = m3.group(3)
                if m_name in MONTHS_MAP:
                    m_num = MONTHS_MAP[m_name]
                    y = int(y_str) if y_str else (2025 if m_num >= 6 else 2026)
                    if y < 100:
                        y += 2000
                    try:
                        return datetime(y, m_num, d)
                    except ValueError:
                        pass

            # 4. Oct 20 2025, October 20th
            m4 = re.search(r'\b([a-z]+)[\s\-]+(\d{1,2})(?:st|nd|rd|th)?(?:,?[\s\-]+(\d{2,4}))?\b', ql)
            if m4:
                m_name = m4.group(1).lower()
                d = int(m4.group(2))
                y_str = m4.group(3)
                if m_name in MONTHS_MAP:
                    m_num = MONTHS_MAP[m_name]
                    y = int(y_str) if y_str else (2025 if m_num >= 6 else 2026)
                    if y < 100:
                        y += 2000
                    try:
                        return datetime(y, m_num, d)
                    except ValueError:
                        pass
            return None

        # -------------------------------------------------------------
        # 1. Date-based Search (e.g. "any notification on 20 October?")
        # -------------------------------------------------------------
        target_dt = _extract_date_from_text(search_query)
        if target_dt:
            target_date = target_dt.date()
            formatted_target = target_dt.strftime("%d %b %Y")
            matched_date_items = []
            for itm in source_array:
                if not isinstance(itm, dict):
                    continue
                parsed = _parse_dt(itm.get(date_key))
                if parsed and parsed.date() == target_date:
                    matched_date_items.append(itm)

            if not matched_date_items:
                return f"There are no notifications found on **{formatted_target}**."

            lines = [f"📢 **Notifications on {formatted_target}:**\n"]
            for i, itm in enumerate(matched_date_items, 1):
                title = itm.get(title_key, "Notice")
                desc = itm.get(desc_key, "").strip()
                sender = itm.get(sender_key, "").strip()
                entry = f"{i}. **{title}**"
                if sender:
                    entry += f" (*{sender}*)"
                if desc:
                    entry += f"\n   📝 {desc}"
                lines.append(entry)
            return "\n".join(lines)

        # -------------------------------------------------------------
        # 2. Recent / Latest Notification Query
        # -------------------------------------------------------------
        if any(kw in q_lower for kw in ("recent", "latest", "new", "today", "yesterday", "last notice", "last notification")):
            recent_list = self._op_filter_recent_notifications(
                source_array,
                limit=3,
                title_key=title_key,
                desc_key=desc_key,
                date_key=date_key,
                sender_key=sender_key,
                type_key=type_key,
            )
            if not recent_list:
                return "There are no recent notifications available."
            return "📢 **Latest School Notifications:**\n\n" + "\n\n".join(recent_list)

        # -------------------------------------------------------------
        # 3. Sender-Specific Search (e.g. "sent by principal", "admin notice")
        # -------------------------------------------------------------
        matched_by_sender = []
        for itm in source_array:
            if not isinstance(itm, dict):
                continue
            snd = str(itm.get(sender_key, "")).strip().lower()
            if snd and (snd in q_lower or any(w in snd for w in q_lower.split() if len(w) >= 4 and w not in ("sent", "from", "notice", "circular", "notification"))):
                matched_by_sender.append(itm)

        if matched_by_sender:
            lines = [f"📢 **Notifications sent by {matched_by_sender[0].get(sender_key, 'Sender')}:**\n"]
            for i, itm in enumerate(matched_by_sender, 1):
                title = itm.get(title_key, "Notice")
                desc = itm.get(desc_key, "").strip()
                dt_fmt = _format_iso_date(str(itm.get(date_key, "")))
                entry = f"{i}. **{title}** — *{dt_fmt}*"
                if desc:
                    entry += f"\n   📝 {desc}"
                lines.append(entry)
            return "\n".join(lines)

        # -------------------------------------------------------------
        # 4. Subject / Message Keyword Search (e.g. "sports day notification")
        # -------------------------------------------------------------
        NOTICE_STOPWORDS = {
            "what", "when", "is", "the", "are", "on", "in", "at", "for", "held",
            "date", "dates", "timing", "schedule", "start", "starts", "will",
            "does", "do", "we", "have", "tell", "me", "show", "details", "about",
            "day", "of", "to", "please", "can", "you", "my", "our", "school",
            "notification", "notifications", "notice", "notices", "circular", "circulars",
            "announcement", "announcements", "give", "list", "any", "there"
        }

        cleaned_words = [w for w in re.sub(r"[^\w\s]", " ", q_lower).split() if w not in NOTICE_STOPWORDS and len(w) >= 3]

        if not cleaned_words:
            return None

        scored_notices = []
        for itm in source_array:
            if not isinstance(itm, dict):
                continue
            title = str(itm.get(title_key, "")).strip().lower()
            desc = str(itm.get(desc_key, "")).strip().lower()
            score = 0
            for w in cleaned_words:
                if w in title:
                    score += 10
                if w in desc:
                    score += 5
            if score > 0:
                scored_notices.append((score, itm))

        if scored_notices:
            scored_notices.sort(key=lambda x: x[0], reverse=True)
            top_notices = [x[1] for x in scored_notices[:4]]
            lines = ["📢 **Matching School Notifications:**\n"]
            for i, itm in enumerate(top_notices, 1):
                title = itm.get(title_key, "Notice")
                desc = itm.get(desc_key, "").strip()
                sender = itm.get(sender_key, "").strip()
                dt_fmt = _format_iso_date(str(itm.get(date_key, "")))
                entry = f"{i}. **{title}**"
                if sender:
                    entry += f" (*{sender}*)"
                entry += f" — *{dt_fmt}*"
                if desc:
                    entry += f"\n   📝 {desc}"
                lines.append(entry)
            return "\n".join(lines)

        return None

    # ------------------------------------------------------------------
    # Study Materials Operations
    # ------------------------------------------------------------------

    def _op_filter_recent_study_materials(
        self,
        source_array: list,
        limit: int = 3,
        subject_key: str = "subject_name",
        type_key: str = "type",
        desc_key: str = "description",
        doc_key: str = "document_name_url",
        date_key: str = "created_date_time",
        teacher_key: str = "name",
    ) -> str:
        """
        Sort study materials by created_date_time descending and return the top `limit` items.
        """
        from app.router.response_mapper import _format_iso_date

        if not source_array or not isinstance(source_array, list):
            return "No study materials currently available."

        valid_items = [itm for itm in source_array if isinstance(itm, dict)]
        if not valid_items:
            return "No study materials currently available."

        def _sort_key(item: dict) -> str:
            return str(item.get(date_key, "")).strip()

        sorted_items = sorted(valid_items, key=_sort_key, reverse=True)
        top_items = sorted_items[:limit]

        lines = ["📚 **Latest Study Materials & Resources:**\n"]
        for i, itm in enumerate(top_items, 1):
            subj = itm.get(subject_key, "General Subject").strip()
            mat_type = itm.get(type_key, "").strip()
            desc = itm.get(desc_key, "").strip()
            teacher = itm.get(teacher_key, "").strip()
            doc_url = itm.get(doc_key, "").strip()
            dt_raw = itm.get(date_key, "")
            dt_fmt = _format_iso_date(str(dt_raw)) if dt_raw else ""

            type_badge = f"`[{mat_type}]` " if mat_type else ""
            entry = f"{i}. 📖 **{subj}** {type_badge}"
            if teacher:
                entry += f"(*{teacher}*)"
            if dt_fmt:
                entry += f" — *{dt_fmt}*"
            if desc:
                # clean up carriage returns
                clean_desc = desc.replace("\r\n", " ").replace("\n", " ").strip()
                entry += f"\n   📝 {clean_desc}"
            if doc_url:
                filename = doc_url.split("/")[-1]
                entry += f"\n   📎 Attachment: `{filename}`"

            lines.append(entry)

        return "\n".join(lines)

    def _op_filter_study_materials_list(
        self,
        source_array: list,
        subject_key: str = "subject_name",
        type_key: str = "type",
        desc_key: str = "description",
        doc_key: str = "document_name_url",
        date_key: str = "created_date_time",
        teacher_key: str = "name",
    ) -> list[str]:
        """
        Format all study materials into a clean list of strings.
        """
        from app.router.response_mapper import _format_iso_date

        if not source_array or not isinstance(source_array, list):
            return []

        results = []
        for itm in source_array:
            if not isinstance(itm, dict):
                continue
            subj = itm.get(subject_key, "General").strip()
            mat_type = itm.get(type_key, "").strip()
            desc = itm.get(desc_key, "").strip()
            teacher = itm.get(teacher_key, "").strip()
            doc_url = itm.get(doc_key, "").strip()
            dt_raw = itm.get(date_key, "")
            dt_fmt = _format_iso_date(str(dt_raw)) if dt_raw else ""

            type_badge = f"`[{mat_type}]` " if mat_type else ""
            entry = f"📖 **{subj}** {type_badge}"
            if teacher:
                entry += f"(*{teacher}*)"
            if dt_fmt:
                entry += f" — *{dt_fmt}*"
            if desc:
                clean_desc = desc.replace("\r\n", " ").replace("\n", " ").strip()
                entry += f"\n   📝 {clean_desc}"
            if doc_url:
                filename = doc_url.split("/")[-1]
                entry += f"\n   📎 `{filename}`"
            results.append(entry)

        return results

    def _op_dynamic_study_material_search(
        self,
        source_array: list,
        query_text: str,
        subject_key: str = "subject_name",
        type_key: str = "type",
        desc_key: str = "description",
        doc_key: str = "document_name_url",
        date_key: str = "created_date_time",
        teacher_key: str = "name",
    ) -> Optional[str]:
        """
        Dynamic handler for study materials queries:
        1. Total / Subject-wise Count (e.g. "how many Kannada study materials", "materials for Kannada and English")
        2. Subject Search (e.g. "Kannada study material", "Show Hindi worksheets")
        3. Type filter (Portions, Worksheets, Notes)
        4. Recent / Latest search (e.g. "latest study material")
        5. Teacher upload search (e.g. "uploaded by Ms Meena")
        """
        from app.router.response_mapper import _format_iso_date
        import re

        if not source_array or not isinstance(source_array, list):
            return "No study materials are currently available in your portal."

        q_lower = query_text.lower().strip()

        # Known subject names
        KNOWN_SUBJECTS = [
            "kannada recitation", "kannada", "hindi", "english", "mathematics", "maths", "math",
            "science", "social studies", "social science", "social", "evs", "computer science",
            "computer", "physics", "chemistry", "biology", "history", "geography", "civics",
            "economics", "french", "sanskrit", "general knowledge", "gk", "moral science",
            "art", "craft", "music", "physical education", "pe"
        ]

        # Find all mentioned subjects in query
        matched_subjects = []
        for subj in KNOWN_SUBJECTS:
            pattern = r'\b' + re.escape(subj) + r'\b'
            if re.search(pattern, q_lower):
                matched_subjects.append(subj)

        # Remove substring overlaps (e.g. keep "kannada recitation" and remove "kannada" if both match)
        if len(matched_subjects) > 1:
            filtered_subjs = []
            for s1 in matched_subjects:
                if not any(s1 != s2 and s1 in s2 for s2 in matched_subjects):
                    filtered_subjs.append(s1)
            matched_subjects = filtered_subjs

        # Check if user is asking for a count
        is_count_query = any(cq in q_lower for cq in ("how many", "how much", "count", "total count", "number of"))

        # -------------------------------------------------------------
        # 1. Subject Count Queries
        # -------------------------------------------------------------
        if is_count_query:
            if matched_subjects:
                if len(matched_subjects) == 1:
                    target_subj = matched_subjects[0]
                    subj_items = [
                        itm for itm in source_array
                        if isinstance(itm, dict) and target_subj in str(itm.get(subject_key, "")).lower()
                    ]
                    count = len(subj_items)
                    return f"You have **{count}** study material(s) available for **{target_subj.title()}**."
                else:
                    counts_breakdown = []
                    total_matched = 0
                    for target_subj in matched_subjects:
                        subj_items = [
                            itm for itm in source_array
                            if isinstance(itm, dict) and target_subj in str(itm.get(subject_key, "")).lower()
                        ]
                        c = len(subj_items)
                        total_matched += c
                        counts_breakdown.append(f"• **{target_subj.title()}**: {c} material(s)")
                    return (
                        f"Study material count for requested subjects:\n\n"
                        + "\n".join(counts_breakdown)
                        + f"\n\n📊 **Total Combined:** {total_matched} material(s)"
                    )
            else:
                total_count = sum(1 for itm in source_array if isinstance(itm, dict))
                return f"You have a total of **{total_count}** study material(s) across all subjects."

        # -------------------------------------------------------------
        # 2. Subject Specific List (e.g. "Kannada study material", "Any notes for Hindi?")
        # -------------------------------------------------------------
        if matched_subjects:
            matching_items = []
            for itm in source_array:
                if not isinstance(itm, dict):
                    continue
                item_subj = str(itm.get(subject_key, "")).lower()
                for target_subj in matched_subjects:
                    if target_subj in item_subj:
                        matching_items.append(itm)
                        break

            if matching_items:
                subj_display = ", ".join(s.title() for s in matched_subjects)
                lines = [f"📚 **Study Materials for {subj_display}:**\n"]
                for i, itm in enumerate(matching_items, 1):
                    subj = itm.get(subject_key, "General").strip()
                    mat_type = itm.get(type_key, "").strip()
                    desc = itm.get(desc_key, "").strip()
                    teacher = itm.get(teacher_key, "").strip()
                    doc_url = itm.get(doc_key, "").strip()
                    dt_raw = itm.get(date_key, "")
                    dt_fmt = _format_iso_date(str(dt_raw)) if dt_raw else ""

                    type_badge = f"`[{mat_type}]` " if mat_type else ""
                    entry = f"{i}. 📖 **{subj}** {type_badge}"
                    if teacher:
                        entry += f"(*{teacher}*)"
                    if dt_fmt:
                        entry += f" — *{dt_fmt}*"
                    if desc:
                        clean_desc = desc.replace("\r\n", " ").replace("\n", " ").strip()
                        entry += f"\n   📝 {clean_desc}"
                    if doc_url:
                        filename = doc_url.split("/")[-1]
                        entry += f"\n   📎 Attachment: `{filename}`"
                    lines.append(entry)
                return "\n".join(lines)
            else:
                subj_display = ", ".join(s.title() for s in matched_subjects)
                return f"No study materials found for **{subj_display}**."

        # -------------------------------------------------------------
        # 3. Material Type Filter (Portions, Worksheets, Notes, Assignments)
        # -------------------------------------------------------------
        KNOWN_TYPES = ["portions", "portion", "worksheets", "worksheet", "notes", "note", "assignment", "assignments", "question bank"]
        matched_type = None
        for t in KNOWN_TYPES:
            if t in q_lower:
                matched_type = t
                break

        if matched_type:
            type_singular = matched_type.rstrip("s")
            matching_items = [
                itm for itm in source_array
                if isinstance(itm, dict) and type_singular in str(itm.get(type_key, "")).lower()
            ]
            if matching_items:
                lines = [f"📚 **Study Materials (`{matched_type.title()}`):**\n"]
                for i, itm in enumerate(matching_items, 1):
                    subj = itm.get(subject_key, "General").strip()
                    mat_type = itm.get(type_key, "").strip()
                    desc = itm.get(desc_key, "").strip()
                    teacher = itm.get(teacher_key, "").strip()
                    doc_url = itm.get(doc_key, "").strip()
                    dt_raw = itm.get(date_key, "")
                    dt_fmt = _format_iso_date(str(dt_raw)) if dt_raw else ""

                    entry = f"{i}. 📖 **{subj}** `[{mat_type}]`"
                    if teacher:
                        entry += f" (*{teacher}*)"
                    if dt_fmt:
                        entry += f" — *{dt_fmt}*"
                    if desc:
                        clean_desc = desc.replace("\r\n", " ").replace("\n", " ").strip()
                        entry += f"\n   📝 {clean_desc}"
                    if doc_url:
                        filename = doc_url.split("/")[-1]
                        entry += f"\n   📎 Attachment: `{filename}`"
                    lines.append(entry)
                return "\n".join(lines)

        # -------------------------------------------------------------
        # 4. Recent / Latest Query (e.g. "latest study material", "recent notes")
        # -------------------------------------------------------------
        if any(w in q_lower for w in ("latest", "recent", "new", "newest", "last")):
            return self._op_filter_recent_study_materials(
                source_array, limit=3,
                subject_key=subject_key, type_key=type_key,
                desc_key=desc_key, doc_key=doc_key,
                date_key=date_key, teacher_key=teacher_key
            )

        # -------------------------------------------------------------
        # 5. Teacher Match (e.g. "uploaded by Ms Meena")
        # -------------------------------------------------------------
        teacher_match = []
        for itm in source_array:
            if not isinstance(itm, dict):
                continue
            teacher = str(itm.get(teacher_key, "")).lower()
            teacher_words = [w for w in re.sub(r"[^\w\s]", "", teacher).split() if len(w) >= 3 and w not in ("ms", "mrs", "mr", "dr", "prof")]
            if any(w in q_lower for w in teacher_words):
                teacher_match.append(itm)

        if teacher_match:
            lines = ["📚 **Study Materials Uploaded by Teacher:**\n"]
            for i, itm in enumerate(teacher_match, 1):
                subj = itm.get(subject_key, "General").strip()
                mat_type = itm.get(type_key, "").strip()
                desc = itm.get(desc_key, "").strip()
                teacher = itm.get(teacher_key, "").strip()
                doc_url = itm.get(doc_key, "").strip()
                dt_raw = itm.get(date_key, "")
                dt_fmt = _format_iso_date(str(dt_raw)) if dt_raw else ""

                type_badge = f"`[{mat_type}]` " if mat_type else ""
                entry = f"{i}. 📖 **{subj}** {type_badge}(*{teacher}*)"
                if dt_fmt:
                    entry += f" — *{dt_fmt}*"
                if desc:
                    clean_desc = desc.replace("\r\n", " ").replace("\n", " ").strip()
                    entry += f"\n   📝 {clean_desc}"
                if doc_url:
                    filename = doc_url.split("/")[-1]
                    entry += f"\n   📎 Attachment: `{filename}`"
                lines.append(entry)
            return "\n".join(lines)

        # Fallback to recent study materials
        return self._op_filter_recent_study_materials(
            source_array, limit=3,
            subject_key=subject_key, type_key=type_key,
            desc_key=desc_key, doc_key=doc_key,
            date_key=date_key, teacher_key=teacher_key
        )


# Singleton
array_aggregator = ArrayAggregator()

