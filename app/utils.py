from __future__ import annotations

import calendar
import json
import re
from datetime import date, datetime, timedelta
from xml.dom import minidom

import black
import markdown
import sqlparse
import yaml
from markupsafe import Markup

FENCED_CODE_RE = re.compile(r"```([a-zA-Z0-9_+\-#.]+)?\n(.*?)```", re.DOTALL)

PYTHON_ALIASES = {"py", "python", "py3", "python3"}
JSON_ALIASES = {"json"}
SQL_ALIASES = {"sql", "mysql", "postgresql", "sqlite"}
YAML_ALIASES = {"yaml", "yml"}
HTML_ALIASES = {"html", "htm", "xml", "svg"}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def today_local() -> date:
    return date.today()


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
    text = format_markdown_code_blocks(value)
    html = markdown.markdown(
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
    return Markup(html)
