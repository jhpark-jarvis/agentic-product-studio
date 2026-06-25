from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta

import markdown
from markupsafe import Markup


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


def markdown_to_html(value: str | None) -> Markup:
    text = value or ""
    html = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
    )
    return Markup(html)
