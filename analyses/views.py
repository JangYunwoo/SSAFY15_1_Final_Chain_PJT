from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from api_utils import api_error, api_ok, form_errors, serialize_datetime, serialize_decimal
from notifications.models import Notification

from .forms import BatchUploadForm
from .models import AnalysisBatch, Lot, ModelVersion, ProcessRecommendation, WaferAnalysis, WaferLabel
from .services.batch_parser import parse_batch_csv
from .services.classifier import predict_wafer_map
from .services.llm_advisor import generate_advice
from .services.recommender import build_summary, recommend_processes
from .services.wafer_renderer import render_wafer_map_png


@login_required
def spa(request, *args, **kwargs):
    return render(request, "base.html")


def make_analysis_code():
    today = timezone.localdate().strftime("%Y%m%d")
    count = WaferAnalysis.objects.filter(created_at__date=timezone.localdate()).count() + 1
    return f"ANL{today}-{count:03d}"


def make_batch_code():
    today = timezone.localdate().strftime("%Y%m%d")
    count = AnalysisBatch.objects.filter(created_at__date=timezone.localdate()).count() + 1
    return f"BAT{today}-{count:03d}"


def accessible_batches(user):
    batches = AnalysisBatch.objects.select_related("lot", "created_by")
    if user.is_staff:
        return batches
    return batches.filter(lot__assignments__user=user).distinct()


def accessible_analyses(user):
    analyses = WaferAnalysis.objects.select_related("lot", "batch", "user")
    if user.is_staff:
        return analyses
    return analyses.filter(lot__assignments__user=user).distinct()


def serialize_lot(lot):
    return {
        "id": lot.id,
        "lotId": lot.lot_id,
        "productCode": lot.product_code,
        "process": lot.process,
        "status": lot.status,
        "startedAt": serialize_datetime(lot.started_at),
        "dueAt": serialize_datetime(lot.due_at),
    }


def serialize_recommendation(item):
    return {
        "rank": item.rank,
        "process": item.process,
        "score": serialize_decimal(item.score),
        "reason": item.reason,
        "stopAlert": item.stop_alert,
    }


def serialize_batch(batch, include_analyses=False):
    data = {
        "id": batch.id,
        "batchCode": batch.batch_code,
        "lot": serialize_lot(batch.lot),
        "status": batch.status,
        "totalWafers": batch.total_wafers,
        "lowConfidenceCount": batch.low_confidence_count,
        "failedMessage": batch.failed_message,
        "createdAt": serialize_datetime(batch.created_at),
    }
    if include_analyses:
        data["analyses"] = [
            serialize_analysis(item)
            for item in batch.wafer_analyses.select_related("lot", "batch", "user")
        ]
    return data


def serialize_analysis(analysis, include_detail=False):
    data = {
        "id": analysis.id,
        "analysisCode": analysis.analysis_code,
        "waferId": analysis.wafer_id,
        "waferIndex": analysis.wafer_index,
        "lot": serialize_lot(analysis.lot) if analysis.lot else None,
        "batchId": analysis.batch_id,
        "status": analysis.status,
        "predictedLabel": analysis.predicted_label,
        "confidence": serialize_decimal(analysis.confidence),
        "confidencePercent": analysis.confidence_percent,
        "isLowConfidence": analysis.is_low_confidence,
        "process": analysis.process,
        "step": analysis.step,
        "equipmentId": analysis.equipment_id,
        "recipeId": analysis.recipe_id,
        "inspectionTime": serialize_datetime(analysis.inspection_time),
        "dieSize": serialize_decimal(analysis.die_size),
        "yieldRate": serialize_decimal(analysis.yield_rate),
        "modelVersion": analysis.model_version,
        "summary": analysis.summary,
        "createdAt": serialize_datetime(analysis.created_at),
        "waferImage": analysis.wafer_image.url if analysis.wafer_image else "",
    }
    if include_detail:
        data["waferMap"] = analysis.wafer_map_json
        data["recommendations"] = [serialize_recommendation(item) for item in analysis.recommendations.all()]
    return data


@login_required
def api_lots(request):
    lots = Lot.objects.all() if request.user.is_staff else Lot.objects.filter(assignments__user=request.user).distinct()
    return api_ok({"lots": [serialize_lot(lot) for lot in lots]})


@login_required
@require_http_methods(["POST"])
def api_upload(request):
    form = BatchUploadForm(request.POST, request.FILES, user=request.user)
    if not form.is_valid():
        return api_error("업로드 정보를 확인해주세요.", errors=form_errors(form))

    batch = form.save(commit=False)
    batch.created_by = request.user
    batch.batch_code = make_batch_code()
    batch.status = AnalysisBatch.STATUS_PENDING
    batch.save()

    try:
        rows = parse_batch_csv(batch.uploaded_file.path)
        if not rows:
            raise ValueError("분석할 웨이퍼 데이터가 없습니다.")

        for row in rows:
            if row.lot_id and row.lot_id != batch.lot.lot_id:
                raise ValueError(f"CSV LOT({row.lot_id})이 선택한 LOT({batch.lot.lot_id})와 다릅니다.")

            analysis = WaferAnalysis.objects.create(
                batch=batch,
                lot=batch.lot,
                user=request.user,
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
            user=request.user,
            type="analysis",
            title="배치 분석 완료",
            body=f"{batch.batch_code} 배치에서 {batch.total_wafers}개 웨이퍼 분석이 완료되었습니다.",
        )
    except Exception as exc:
        batch.status = AnalysisBatch.STATUS_FAILED
        batch.failed_message = str(exc)
        batch.save(update_fields=["status", "failed_message"])
        return api_error(str(exc), status=500, errors={"batchId": batch.id})

    return api_ok({"batch": serialize_batch(batch, include_analyses=True)}, status=201)


@login_required
def api_history(request):
    analyses = accessible_analyses(request.user)
    label = request.GET.get("label")
    if label:
        analyses = analyses.filter(predicted_label=label)
    batches = accessible_batches(request.user)[:20]
    labels = list(WaferLabel.objects.values("label", "description"))
    return api_ok(
        {
            "analyses": [serialize_analysis(item) for item in analyses],
            "batches": [serialize_batch(item) for item in batches],
            "labels": labels,
        }
    )


@login_required
def api_batch_detail(request, pk):
    batch = get_object_or_404(accessible_batches(request.user), pk=pk)
    return api_ok({"batch": serialize_batch(batch, include_analyses=True)})


@login_required
def api_detail(request, pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=pk)
    return api_ok({"analysis": serialize_analysis(analysis, include_detail=True)})


@login_required
def api_model_performance(request):
    versions = [
        {
            "id": item.id,
            "modelName": item.model_name,
            "version": item.version,
            "f1Score": serialize_decimal(item.f1_score),
            "registeredAt": item.registered_at.isoformat() if item.registered_at else None,
            "isActive": item.is_active,
            "notes": item.notes,
        }
        for item in ModelVersion.objects.all()
    ]
    label_counts = list(WaferAnalysis.objects.values("predicted_label").annotate(total=Count("id")).order_by("-total"))
    return api_ok({"versions": versions, "labelCounts": label_counts})
