from pathlib import Path

from django.core.files import File
from django.db import transaction
from django.utils import timezone

from analyses.models import AnalysisBatch, Lot, ProcessRecommendation, WaferAnalysis
from analyses.services.batch_parser import parse_batch_csv
from analyses.services.classifier import predict_wafer_map
from analyses.services.llm_advisor import generate_advice
from analyses.services.recommender import build_summary, recommend_processes
from analyses.services.wafer_renderer import render_wafer_map_png
from notifications.models import Notification


def make_analysis_code():
    today = timezone.localdate().strftime("%Y%m%d")
    count = WaferAnalysis.objects.filter(created_at__date=timezone.localdate()).count() + 1
    return f"ANL{today}-{count:03d}"


def make_batch_code():
    today = timezone.localdate().strftime("%Y%m%d")
    count = AnalysisBatch.objects.filter(created_at__date=timezone.localdate()).count() + 1
    return f"BAT{today}-{count:03d}"


def analyze_batch_rows(batch, rows, user):
    if not rows:
        raise ValueError("분석할 웨이퍼 데이터가 없습니다.")

    for row in rows:
        if row.lot_id and row.lot_id != batch.lot.lot_id:
            raise ValueError(f"CSV LOT({row.lot_id})이 선택한 LOT({batch.lot.lot_id})와 다릅니다.")

        analysis = WaferAnalysis.objects.create(
            batch=batch,
            lot=batch.lot,
            user=user,
            analysis_code=make_analysis_code(),
            uploaded_file=batch.uploaded_file.name,
            status=WaferAnalysis.STATUS_PENDING,
            wafer_id=row.wafer_id,
            wafer_index=row.wafer_index,
            process=row.process or batch.lot.process,
            step=row.step,
            equipment_id=row.equipment_id,
            recipe_id=row.recipe_id,
            inspection_time=row.inspection_time,
            die_size=row.die_size,
            yield_rate=row.yield_rate,
            wafer_map_json=row.wafer_map.tolist(),
        )

        wafer_png = render_wafer_map_png(row.wafer_map)
        if wafer_png is not None:
            analysis.wafer_image.save(f"{analysis.analysis_code}.png", wafer_png, save=False)

        result = predict_wafer_map(row.wafer_map)
        recommendations = recommend_processes(result.label, result.confidence)
        analysis.predicted_label = result.label
        analysis.confidence = result.confidence
        analysis.probabilities_json = result.probabilities
        analysis.status = WaferAnalysis.STATUS_DONE
        analysis.summary = generate_advice(analysis, recommendations)
        analysis.save()

        for item in recommendations:
            ProcessRecommendation.objects.create(analysis=analysis, **item)

        if not analysis.summary:
            analysis.summary = build_summary(analysis)
            analysis.save(update_fields=["summary"])

    batch.total_wafers = len(rows)
    batch.status = AnalysisBatch.STATUS_DONE
    batch.save(update_fields=["total_wafers", "status"])
    Notification.objects.create(
        user=user,
        type="analysis",
        title="배치 분석 완료",
        body=f"{batch.batch_code} 배치에서 {batch.total_wafers}개 웨이퍼 분석이 완료되었습니다.",
    )
    return batch


def analyze_existing_batch(batch, user):
    try:
        rows = parse_batch_csv(batch.uploaded_file.path)
        return analyze_batch_rows(batch, rows, user)
    except Exception:
        batch.status = AnalysisBatch.STATUS_FAILED
        batch.failed_message = "분석 처리 중 오류가 발생했습니다."
        batch.save(update_fields=["status", "failed_message"])
        raise


def find_lot_for_rows(rows):
    lot_ids = {row.lot_id for row in rows if row.lot_id}
    if len(lot_ids) != 1:
        raise ValueError("CSV에는 하나의 lot_id만 포함되어야 합니다.")
    lot_id = lot_ids.pop()
    try:
        return Lot.objects.get(lot_id=lot_id)
    except Lot.DoesNotExist as exc:
        raise ValueError(f"DB에 LOT({lot_id})가 없습니다.") from exc


@transaction.atomic
def create_batch_from_csv_file(file_path, user):
    source = Path(file_path)
    rows = parse_batch_csv(source)
    lot = find_lot_for_rows(rows)

    batch = AnalysisBatch(
        batch_code=make_batch_code(),
        lot=lot,
        created_by=user,
        status=AnalysisBatch.STATUS_PENDING,
    )
    with source.open("rb") as csv_file:
        batch.uploaded_file.save(source.name, File(csv_file), save=True)

    try:
        return analyze_batch_rows(batch, rows, user)
    except Exception as exc:
        batch.status = AnalysisBatch.STATUS_FAILED
        batch.failed_message = str(exc)
        batch.save(update_fields=["status", "failed_message"])
        raise
