from __future__ import annotations

import csv
from pathlib import Path


REQUIRED_COLUMNS = {
    "asset_type",
    "gender",
    "name",
    "master_resource_id",
    "variant_resource_id",
}


def load_avatar_catalog_records(input_path: str | Path):
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Avatar catalog source file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - fieldnames
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Avatar catalog source is missing columns: {missing}")

        records = []
        for row_number, row in enumerate(reader, start=2):
            record = {key: (value or "").strip() for key, value in row.items()}
            if record["asset_type"] not in {"hair", "face"}:
                raise ValueError(
                    f"Invalid asset_type at row {row_number}: {record['asset_type']}"
                )
            if record["gender"] not in {"male", "female"}:
                raise ValueError(
                    f"Invalid gender at row {row_number}: {record['gender']}"
                )
            if (
                not record["name"]
                or not record["master_resource_id"]
                or not record["variant_resource_id"]
            ):
                raise ValueError(
                    f"Required avatar catalog value is empty at row {row_number}"
                )
            records.append(record)

    return records
