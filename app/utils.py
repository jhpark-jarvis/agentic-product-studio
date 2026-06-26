from __future__ import annotations

import calendar
import json
import re
from datetime import date, datetime, timedelta, timezone
from xml.dom import minidom
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

import black
import markdown
import sqlparse
import yaml
from markupsafe import Markup

FENCED_CODE_RE = re.compile(r"```([a-zA-Z0-9_+\-#.]+)?\n(.*?)```", re.DOTALL)
DETAILS_RE = re.compile(
    r"<details(?P<attrs>[^>]*)>\s*<summary>(?P<summary>.*?)</summary>(?P<body>.*?)</details>",
    re.DOTALL | re.IGNORECASE,
)

PYTHON_ALIASES = {"py", "python", "py3", "python3"}
JSON_ALIASES = {"json"}
SQL_ALIASES = {"sql", "mysql", "postgresql", "sqlite"}
YAML_ALIASES = {"yaml", "yml"}
HTML_ALIASES = {"html", "htm", "xml", "svg"}
DEFAULT_TIMEZONE = "Asia/Seoul"
WBS_PLATFORM_OPTIONS = ["Agentic Product Studio", "외부 에셋 카탈로그(게임 제작)"]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _timezone(tz_name: str | None = None):
    name = tz_name or DEFAULT_TIMEZONE
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == "UTC":
            return timezone.utc
        if name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=9))
        return timezone.utc


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=_timezone("UTC"))
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=_timezone("UTC"))
        return parsed
    except ValueError:
        return None


def today_local() -> date:
    return datetime.now(_timezone()).date()


def week_bounds(reference: date | None = None) -> tuple[date, date]:
    current = reference or today_local()
    start = current - timedelta(days=current.weekday())
    end = start + timedelta(days=6)
    return start, end


def month_bounds(reference: date | None = None) -> tuple[date, date]:
    current = reference or today_local()
    start = current.replace(day=1)
    _, last_day = calendar.monthrange(current.year, current.month)
    end = current.replace(day=last_day)
    return start, end


def format_datetime_local(value: str | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    parsed = parse_timestamp(value)
    if not parsed:
        return value or "-"
    return parsed.astimezone(_timezone()).strftime(fmt)


def parse_int(value, default: int, allowed: set[int] | None = None, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None and parsed < minimum:
        return default
    if allowed is not None and parsed not in allowed:
        return default
    return parsed


def build_pagination(page: int, per_page: int, total_count: int) -> dict[str, int | bool]:
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    current_page = min(max(page, 1), total_pages)
    return {
        "page": current_page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_page": current_page - 1,
        "next_page": current_page + 1,
        "offset": (current_page - 1) * per_page,
    }


def _build_markdown_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "sane_lists", "nl2br"],
        extension_configs={
            "codehilite": {
                "guess_lang": False,
                "use_pygments": True,
                "noclasses": False,
            }
        },
    )


def _strip_wrapping_paragraph(html: str) -> str:
    stripped = html.strip()
    if stripped.startswith("<p>") and stripped.endswith("</p>") and stripped.count("<p>") == 1:
        return stripped[3:-4]
    return stripped


def _render_details_blocks(text: str) -> str:
    source = text or ""

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs") or ""
        summary = (match.group("summary") or "").strip()
        body = (match.group("body") or "").strip()
        rendered_summary = _strip_wrapping_paragraph(_build_markdown_html(format_markdown_code_blocks(summary)))
        rendered_body = _render_markdown_with_details(body)
        return (
            f"<details{attrs}>"
            f"<summary>{rendered_summary}</summary>"
            f"{rendered_body}"
            f"</details>"
        )

    previous = None
    while previous != source:
        previous = source
        source = DETAILS_RE.sub(replace, source)
    return source


def _render_markdown_with_details(text: str) -> str:
    prepared = _render_details_blocks(format_markdown_code_blocks(text))
    return _build_markdown_html(prepared)


def css_badge_class(value: str | None, kind: str = "status") -> str:
    token = (value or "").strip().lower()

    if kind == "priority":
        if "긴급" in token or "urgent" in token:
            return "badge--priority-urgent"
        if "높" in token or "high" in token:
            return "badge--priority-high"
        if "보통" in token or "medium" in token or "normal" in token:
            return "badge--priority-medium"
        if "낮" in token or "low" in token:
            return "badge--priority-low"
        return "badge--priority"

    if "완료" in token or "done" in token or "complete" in token:
        return "badge--done"
    if "검토" in token or "review" in token:
        return "badge--review"
    if "진행" in token or "progress" in token or "doing" in token:
        return "badge--in-progress"
    if "보류" in token or "hold" in token or "pause" in token:
        return "badge--hold"
    if "예정" in token or "plan" in token or "todo" in token:
        return "badge--planned"
    return "badge--status"


def format_code_block(language: str | None, code: str) -> str:
    lang = (language or "").strip().lower()
    stripped = code.strip("\n")

    if not stripped:
        return code

    try:
        if lang in PYTHON_ALIASES:
            return black.format_str(stripped, mode=black.Mode())

        if lang in JSON_ALIASES:
            parsed = json.loads(stripped)
            return json.dumps(parsed, indent=2, ensure_ascii=False)

        if lang in SQL_ALIASES:
            return sqlparse.format(stripped, reindent=True, keyword_case="upper")

        if lang in YAML_ALIASES:
            parsed = yaml.safe_load(stripped)
            return yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True).rstrip()

        if lang in HTML_ALIASES:
            parsed = minidom.parseString(stripped.encode("utf-8"))
            pretty = parsed.toprettyxml(indent="  ")
            lines = [line for line in pretty.splitlines() if line.strip()]
            return "\n".join(lines)
    except Exception:
        return code

    return code


def format_markdown_code_blocks(text: str | None) -> str:
    source = text or ""

    def replace(match: re.Match[str]) -> str:
        language = (match.group(1) or "").strip()
        code = match.group(2)
        formatted = format_code_block(language, code)
        suffix = "\n" if not formatted.endswith("\n") else ""
        if language:
            return f"```{language}\n{formatted}{suffix}```"
        return f"```\n{formatted}{suffix}```"

    return FENCED_CODE_RE.sub(replace, source)


def markdown_to_html(value: str | None) -> Markup:
    return Markup(_render_markdown_with_details(value or ""))
