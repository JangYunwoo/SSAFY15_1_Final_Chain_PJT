from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import csv

from django.utils import timezone

from .classifier import parse_wafer_value


@dataclass
class WaferCsvRow:
    lot_id: str
    wafer_id: str
    wafer_index: int | None
    process: str
    step: str
    equipment_id: str
    recipe_id: str
    inspection_time: datetime | None
    die_size: Decimal | None
    yield_rate: Decimal | None
    wafer_map: object


def _get(row, *names, default=""):
    lowered = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ""):
            return value
    return default


def _to_int(value):
    try:
        return int(float(value)) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _to_decimal(value):
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def calculate_yield_rate(wafer_map):
    values = [float(value) for row in wafer_map for value in row]
    passed = sum(value == 1.0 for value in values)
    failed = sum(value == 2.0 for value in values)
    total = passed + failed
    return Decimal(str(round(passed / total * 100, 2))) if total else None


def _to_datetime(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            pass
    return None


def parse_batch_csv(file_path):
    rows = []
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        field_names = {name.lower() for name in reader.fieldnames or []}
        if not reader.fieldnames or not {"wafer_map", "wafermap"}.intersection(field_names):
            raise ValueError("LOT CSV에는 wafer_map 또는 waferMap 컬럼이 필요합니다.")

        for idx, row in enumerate(reader, start=1):
            wafer_map = parse_wafer_value(_get(row, "wafer_map", "waferMap"))
            if wafer_map is None:
                raise ValueError(f"{idx}번째 행의 wafer_map을 읽을 수 없습니다.")

            rows.append(
                WaferCsvRow(
                    lot_id=_get(row, "lot_id", "lotName", "lot_name"),
                    wafer_id=_get(row, "wafer_id", "waferId", default=f"WAFER-{idx:03d}"),
                    wafer_index=_to_int(_get(row, "wafer_index", "waferIndex", default=idx)),
                    process=_get(row, "process"),
                    step=_get(row, "step"),
                    equipment_id=_get(row, "equipment_id", "equipmentId"),
                    recipe_id=_get(row, "recipe_id", "recipeId"),
                    inspection_time=_to_datetime(_get(row, "inspection_time", "inspectionTime")),
                    die_size=_to_decimal(_get(row, "die_size", "dieSize")),
                    yield_rate=_to_decimal(_get(row, "yield_rate", "yieldRate")) or calculate_yield_rate(wafer_map),
                    wafer_map=wafer_map,
                )
            )
    return rows
