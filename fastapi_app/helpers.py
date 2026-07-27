from __future__ import annotations

import re

from app.constants import ASSET_TYPES


PER_PAGE_OPTIONS = (10, 20, 50, 100)


def serialize_rows(rows):
    return [dict(row) for row in rows]


def row_value(row, key, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    mapping = dict(row)
    return mapping.get(key, default)


DOCUMENT_LINK_PATTERN = re.compile(
    r"(?:https?://[^\s)\"'>]+)?/documents?/(?P<document_id>\d+)(?=[/?#)\]\s\"'<>]|$)",
    re.IGNORECASE,
)


def extract_linked_document_ids(content: str, current_document_id: int, *, parse_int):
    ordered_ids: list[int] = []
    seen_ids: set[int] = set()

    for match in DOCUMENT_LINK_PATTERN.finditer(content or ""):
        document_id = parse_int(match.group("document_id"), default=0, minimum=1)
        if not document_id or document_id == current_document_id or document_id in seen_ids:
            continue
        seen_ids.add(document_id)
        ordered_ids.append(document_id)

    return ordered_ids


def asset_type_options(provider):
    repository_options = [
        row_value(row, "asset_type", "")
        for row in provider.assets.fetch_asset_type_options()
        if str(row_value(row, "asset_type", "") or "").strip()
    ]
    merged = []
    for option in [*ASSET_TYPES, *repository_options]:
        normalized = (option or "").strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def build_asset_group_tree(rows):
    nodes_by_path: dict[str, dict] = {}
    roots: list[dict] = []

    for row in rows:
        path = str(row_value(row, "path", "") or "").strip()
        if not path:
            continue
        node = {
            "path": path,
            "name": path.split("/")[-1],
            "direct_asset_count": int(row_value(row, "direct_asset_count", 0) or 0),
            "total_asset_count": int(row_value(row, "direct_asset_count", 0) or 0),
            "last_updated_at": row_value(row, "last_updated_at"),
            "is_explicit": bool(row_value(row, "is_explicit")),
            "children": [],
        }
        nodes_by_path[path] = node

    for path in sorted(nodes_by_path.keys(), key=lambda value: (value.count("/"), value.lower())):
        node = nodes_by_path[path]
        parent_path = "/".join(path.split("/")[:-1])
        parent = nodes_by_path.get(parent_path)
        if parent:
            parent["children"].append(node)
        else:
            roots.append(node)

    def accumulate(node: dict):
        total = node["direct_asset_count"]
        for child in node["children"]:
            total += accumulate(child)
        node["total_asset_count"] = total
        node["children"].sort(key=lambda item: item["name"].lower())
        return total

    for root in roots:
        accumulate(root)
    roots.sort(key=lambda item: item["name"].lower())
    return roots


def asset_group_payload(provider, *, include_hidden: bool):
    group_rows = provider.assets.fetch_asset_groups(include_hidden=include_hidden)
    category_rows = provider.assets.fetch_category_options(include_hidden=include_hidden)
    ungrouped_count = 0
    for row in category_rows:
        if row_value(row, "category") == "미분류":
            ungrouped_count = int(row_value(row, "asset_count", 0) or 0)
            break
    return {
        "tree": build_asset_group_tree(group_rows),
        "ungrouped_asset_count": ungrouped_count,
    }
