from __future__ import annotations

import json
import re
from xml.dom import minidom

import black
import markdown
import sqlparse
import yaml


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


def _render_details_blocks(text: str) -> str:
    source = text or ""

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs") or ""
        summary = (match.group("summary") or "").strip()
        body = (match.group("body") or "").strip()
        rendered_summary = _strip_wrapping_paragraph(_build_markdown_html(format_markdown_code_blocks(summary)))
        rendered_body = render_markdown_html(body)
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


def render_markdown_html(text: str | None) -> str:
    prepared = _render_details_blocks(format_markdown_code_blocks(text or ""))
    return _build_markdown_html(prepared)
