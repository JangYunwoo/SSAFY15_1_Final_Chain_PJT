from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods

from api_utils import api_error, api_ok, form_errors, serialize_datetime, serialize_decimal

from .forms import BatchUploadForm
from .models import AnalysisBatch, Lot, WaferAnalysis, WaferLabel


@login_required
def spa(request, *args, **kwargs):
    return render(request, "base.html")


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


def serialize_prediction_candidates(analysis):
    probabilities = analysis.probabilities_json or {}
    if not probabilities:
        if not analysis.predicted_label:
            return []
        return [
            {
                "rank": 1,
                "label": analysis.predicted_label,
                "probability": float(analysis.confidence),
                "percent": analysis.confidence_percent,
            }
        ]

    top_items = sorted(probabilities.items(), key=lambda item: float(item[1]), reverse=True)[:3]
    return [
        {
            "rank": index,
            "label": label,
            "probability": float(probability),
            "percent": round(float(probability) * 100, 1),
        }
        for index, (label, probability) in enumerate(top_items, start=1)
    ]


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
        "topPredictions": serialize_prediction_candidates(analysis),
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


def save_upload_to_incoming(uploaded_file):
    incoming_dir = Path(settings.BASE_DIR) / "LotData" / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    storage = FileSystemStorage(location=incoming_dir)
    filename = get_valid_filename(uploaded_file.name)
    if storage.exists(filename):
        source_name = Path(filename)
        stamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
        filename = f"{source_name.stem}-{stamp}{source_name.suffix}"

    return storage.save(filename, uploaded_file)


@login_required
@require_http_methods(["POST"])
def api_upload(request):
    form = BatchUploadForm(request.POST, request.FILES, user=request.user)
    if not form.is_valid():
        return api_error("업로드 정보를 확인해주세요.", errors=form_errors(form))

    saved_name = save_upload_to_incoming(form.cleaned_data["uploaded_file"])
    return api_ok(
        {
            "queued": True,
            "incomingFile": saved_name,
            "message": "분석이 시작되었습니다. 잠시 후 분석 이력에서 결과를 확인할 수 있습니다.",
        },
        status=202,
    )


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
