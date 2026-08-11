from __future__ import annotations


def _row_value(row, key, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    return row[key] if key in row.keys() else default


def build_avatar_catalog(rows):
    assets_by_id = {}
    for row in rows:
        asset_id = int(_row_value(row, "asset_id"))
        asset = assets_by_id.get(asset_id)
        if asset is None:
            asset = {
                "id": asset_id,
                "asset_type": _row_value(row, "asset_type", ""),
                "gender": _row_value(row, "gender", ""),
                "name": _row_value(row, "name", ""),
                "source_index": int(_row_value(row, "source_index", 0) or 0),
                "availability": _row_value(row, "availability", ""),
                "match_status": _row_value(row, "match_status", ""),
                "series": _row_value(row, "series", ""),
                "confidence": _row_value(row, "confidence", ""),
                "master_resource_id": _row_value(row, "master_resource_id", ""),
                "group_id": _row_value(row, "group_id", ""),
                "group_size": int(_row_value(row, "group_size", 0) or 0),
                "master_color_hex": _row_value(row, "master_color_hex", ""),
                "master_is_group_canonical": _as_bool(
                    _row_value(row, "master_is_group_canonical", 0)
                ),
                "variants": [],
            }
            assets_by_id[asset_id] = asset

        variant_resource_id = _row_value(row, "variant_resource_id", "")
        if variant_resource_id:
            asset["variants"].append(
                {
                    "resource_id": variant_resource_id,
                    "thumbnail_url": _row_value(row, "thumbnail_url", ""),
                    "hex_code": _row_value(row, "hex_code", ""),
                    "name": _row_value(row, "variant_name", ""),
                    "dname": _row_value(row, "dname", ""),
                }
            )

    return list(assets_by_id.values())


def build_avatar_catalog_query(*, search: str, asset_type: str, gender: str):
    clauses = []
    params = []
    if search:
        like = f"%{search}%"
        clauses.append(
            """(
                a.name LIKE ?
                OR a.master_resource_id LIKE ?
                OR EXISTS (
                    SELECT 1
                    FROM avatar_asset_variants search_variant
                    WHERE search_variant.avatar_asset_id = a.id
                      AND (search_variant.name LIKE ? OR search_variant.resource_id LIKE ?)
                )
            )"""
        )
        params.extend([like, like, like, like])
    if asset_type:
        clauses.append("a.asset_type = ?")
        params.append(asset_type)
    if gender:
        clauses.append("a.gender = ?")
        params.append(gender)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return (
        f"""
        SELECT
            a.id AS asset_id,
            a.asset_type,
            a.gender,
            a.name,
            a.source_index,
            a.availability,
            a.match_status,
            a.series,
            a.confidence,
            a.master_resource_id,
            a.group_id,
            a.group_size,
            a.master_color_hex,
            a.master_is_group_canonical,
            v.resource_id AS variant_resource_id,
            v.thumbnail_url,
            v.hex_code,
            v.name AS variant_name,
            v.dname
        FROM avatar_assets a
        LEFT JOIN avatar_asset_variants v ON v.avatar_asset_id = a.id
        {where_clause}
        ORDER BY a.asset_type ASC, a.source_index ASC, a.name COLLATE NOCASE ASC, a.gender ASC, v.name COLLATE NOCASE ASC
        """,
        params,
    )


def fetch_avatar_catalog(db, *, search: str, asset_type: str, gender: str):
    query, params = build_avatar_catalog_query(
        search=search,
        asset_type=asset_type,
        gender=gender,
    )
    return build_avatar_catalog(db.execute(query, params).fetchall())


def fetch_avatar_catalog_summary(db):
    row = db.execute(
        """
        SELECT
            COUNT(*) AS asset_count,
            SUM(CASE WHEN asset_type = 'hair' THEN 1 ELSE 0 END) AS hair_count,
            SUM(CASE WHEN asset_type = 'face' THEN 1 ELSE 0 END) AS face_count,
            (SELECT COUNT(*) FROM avatar_asset_variants) AS variant_count
        FROM avatar_assets
        """
    ).fetchone()
    return {
        "asset_count": int(_row_value(row, "asset_count", 0) or 0),
        "variant_count": int(_row_value(row, "variant_count", 0) or 0),
        "hair_count": int(_row_value(row, "hair_count", 0) or 0),
        "face_count": int(_row_value(row, "face_count", 0) or 0),
    }


def _as_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def replace_avatar_catalog(db, records, *, replace: bool):
    if replace:
        db.execute("DELETE FROM avatar_asset_variants")
        db.execute("DELETE FROM avatar_assets")

    asset_keys = set()
    variant_count = 0
    for record in records:
        asset_key = (record["asset_type"], record["gender"], record["master_resource_id"])
        asset_keys.add(asset_key)
        db.execute(
            """
            INSERT INTO avatar_assets (
                asset_type, gender, name, source_index, availability, match_status, series, confidence,
                master_resource_id, group_id, group_size, master_color_hex, master_is_group_canonical
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_type, gender, master_resource_id) DO UPDATE SET
                name = excluded.name,
                source_index = excluded.source_index,
                availability = excluded.availability,
                match_status = excluded.match_status,
                series = excluded.series,
                confidence = excluded.confidence,
                group_id = excluded.group_id,
                group_size = excluded.group_size,
                master_color_hex = excluded.master_color_hex,
                master_is_group_canonical = excluded.master_is_group_canonical,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                record["asset_type"],
                record["gender"],
                record["name"],
                int(record.get("source_index") or 0),
                record.get("availability") or "",
                record.get("match_status") or "",
                record.get("series") or "",
                record.get("confidence") or "",
                record["master_resource_id"],
                record.get("group_id") or "",
                int(record.get("group_size") or 0),
                record.get("master_color_hex") or "",
                1 if _as_bool(record.get("master_is_group_canonical")) else 0,
            ),
        )
        asset_row = db.execute(
            "SELECT id FROM avatar_assets WHERE asset_type = ? AND gender = ? AND master_resource_id = ?",
            asset_key,
        ).fetchone()
        asset_id = int(_row_value(asset_row, "id"))
        db.execute(
            """
            INSERT INTO avatar_asset_variants (avatar_asset_id, resource_id, thumbnail_url, hex_code, name, dname)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(avatar_asset_id, resource_id) DO UPDATE SET
                thumbnail_url = excluded.thumbnail_url,
                hex_code = excluded.hex_code,
                name = excluded.name,
                dname = excluded.dname
            """,
            (
                asset_id,
                record["variant_resource_id"],
                record.get("thumbnail_url") or "",
                record.get("hex_code") or "",
                record.get("variant_name") or "",
                record.get("dname") or "",
            ),
        )
        variant_count += 1

    return {"asset_count": len(asset_keys), "variant_count": variant_count}
