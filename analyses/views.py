from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods, require_POST

from api_utils import api_error, api_ok, form_errors, json_body, serialize_datetime, serialize_decimal

from .forms import BatchUploadForm
from .models import AnalysisBatch, CustomAnalysis, Lot, LotAssignment, WaferAnalysis, WaferLabel
from .services.batch_insights import create_batch_insight, create_custom_analysis


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


def serialize_lot_assignment(assignment):
    return {
        "id": assignment.id,
        "lotId": assignment.lot_id,
        "lotName": assignment.lot.lot_id,
        "userId": assignment.user_id,
        "userName": assignment.user.display_name(),
        "userEmail": assignment.user.email,
        "department": assignment.user.department,
        "role": assignment.role,
        "assignedBy": assignment.assigned_by.display_name() if assignment.assigned_by else "-",
        "assignedAt": serialize_datetime(assignment.assigned_at),
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
        "fileName": Path(batch.uploaded_file.name).name if batch.uploaded_file else batch.batch_code,
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
    effective_yield_rate = analysis.effective_yield_rate
    is_normal = effective_yield_rate is not None and effective_yield_rate >= 90
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
        "topPredictions": [] if is_normal else serialize_prediction_candidates(analysis),
        "isNormal": is_normal,
        "isLowConfidence": analysis.is_low_confidence,
        "process": analysis.process,
        "step": analysis.step,
        "equipmentId": analysis.equipment_id,
        "recipeId": analysis.recipe_id,
        "inspectionTime": serialize_datetime(analysis.inspection_time),
        "dieSize": serialize_decimal(analysis.die_size),
        "yieldRate": effective_yield_rate,
        "modelVersion": analysis.model_version,
        "summary": analysis.summary,
        "createdAt": serialize_datetime(analysis.created_at),
        "waferImage": analysis.wafer_image.url if analysis.wafer_image else "",
    }
    if include_detail:
        data["waferMap"] = analysis.wafer_map_json
        data["recommendations"] = [serialize_recommendation(item) for item in analysis.recommendations.all()]
    return data


def serialize_insight(insight):
    return {
        "id": insight.id,
        "title": insight.title,
        "isCustom": insight.is_custom,
        "isFallback": insight.is_fallback,
        "labelDistribution": insight.label_distribution,
        "summary": insight.recommendation_text,
        "recommendations": insight.recommendations_json,
        "report": insight.report_body,
        "createdAt": serialize_datetime(insight.created_at),
    }


def serialize_custom_analysis(custom):
    return {
        "id": custom.id,
        "title": custom.title,
        "isFallback": custom.is_fallback,
        "labelDistribution": custom.label_distribution,
        "summary": custom.recommendation_text,
        "recommendations": custom.recommendations_json,
        "report": custom.report_body,
        "selectedWafers": [serialize_analysis(item) for item in custom.analyses.select_related("lot", "batch")],
        "createdAt": serialize_datetime(custom.created_at),
    }


@login_required
def api_lots(request):
    lots = Lot.objects.all() if request.user.is_staff else Lot.objects.filter(assignments__user=request.user).distinct()
    lots = lots.order_by("lot_id")
    return api_ok({"lots": [serialize_lot(lot) for lot in lots]})


@login_required
@require_http_methods(["GET", "POST"])
def api_lot_assignments(request):
    if not request.user.is_staff:
        return api_error("관리자만 LOT을 배정할 수 있습니다.", status=403)

    User = get_user_model()
    if request.method == "GET":
        lots = Lot.objects.order_by("lot_id")
        users = User.objects.filter(is_active=True, is_staff=False).order_by("name", "username")
        assignments = LotAssignment.objects.select_related("lot", "user", "assigned_by")
        return api_ok({
            "lots": [serialize_lot(lot) for lot in lots],
            "users": [
                {
                    "id": user.id,
                    "displayName": user.display_name(),
                    "email": user.email,
                    "department": user.department,
                }
                for user in users
            ],
            "assignments": [serialize_lot_assignment(item) for item in assignments],
        })

    data = json_body(request)
    lot_id = data.get("lotId")
    user_id = data.get("userId")
    role = data.get("role") or LotAssignment.ROLE_OWNER
    if role not in dict(LotAssignment.ROLE_CHOICES):
        return api_error("배정 역할을 확인해주세요.")

    lot = get_object_or_404(Lot, pk=lot_id)
    user = get_object_or_404(User.objects.filter(is_active=True, is_staff=False), pk=user_id)
    assignment, created = LotAssignment.objects.get_or_create(
        lot=lot,
        user=user,
        defaults={"role": role, "assigned_by": request.user},
    )
    if not created and assignment.role != role:
        assignment.role = role
        if assignment.assigned_by_id is None:
            assignment.assigned_by = request.user
        assignment.save(update_fields=["role", "assigned_by"])
    return api_ok({"assignment": serialize_lot_assignment(assignment), "created": created}, status=201 if created else 200)


@login_required
@require_http_methods(["DELETE"])
def api_lot_assignment_detail(request, pk):
    if not request.user.is_staff:
        return api_error("관리자만 LOT 배정을 해제할 수 있습니다.", status=403)

    assignment = get_object_or_404(LotAssignment, pk=pk)
    assignment.delete()
    return api_ok()


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
            "customAnalyses": [serialize_custom_analysis(item) for item in CustomAnalysis.objects.filter(user=request.user)],
            "labels": labels,
        }
    )


@login_required
def api_batch_detail(request, pk):
    batch = get_object_or_404(accessible_batches(request.user), pk=pk)
    data = serialize_batch(batch, include_analyses=True)
    # 이력 폼에는 하나만 보이되, 실제 GMS 응답이 있으면 fallback보다 우선한다.
    latest_insight = batch.insights.filter(is_fallback=False).order_by("-created_at").first()
    latest_insight = latest_insight or batch.insights.order_by("-created_at").first()
    data["insights"] = [serialize_insight(latest_insight)] if latest_insight else []
    return api_ok({"batch": data})


@login_required
@require_POST
def api_create_batch_insight(request, pk):
    try:
        batch = get_object_or_404(accessible_batches(request.user), pk=pk)
        selected_ids = json_body(request).get("analysisIds", [])
        analyses = batch.wafer_analyses.all()
        is_custom = bool(selected_ids)
        if is_custom:
            analyses = analyses.filter(id__in=selected_ids)
            if analyses.count() != len(set(selected_ids)):
                return api_error("선택한 웨이퍼 중 이 배치에 없는 항목이 있습니다.")
        if not analyses.exists():
            return api_error("분석할 웨이퍼를 한 개 이상 선택해 주세요.")

        insight = create_batch_insight(batch, request.user, analyses=analyses, is_custom=is_custom)
        return api_ok({"insight": serialize_insight(insight)}, status=201)
    except Exception as exc:
        return api_error(f"배치 AI 분석 오류: {exc}", status=500)


@login_required
@require_POST
def api_create_custom_analysis(request):
    selected_ids = json_body(request).get("analysisIds", [])
    if not selected_ids:
        return api_error("분석할 웨이퍼를 한 개 이상 선택해 주세요.")
    analyses = accessible_analyses(request.user).filter(id__in=selected_ids)
    if analyses.count() != len(set(selected_ids)):
        return api_error("선택한 웨이퍼 중 접근할 수 없는 항목이 있습니다.")
    custom = create_custom_analysis(request.user, analyses)
    return api_ok({"customAnalysis": serialize_custom_analysis(custom)}, status=201)


@login_required
def api_detail(request, pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=pk)
    return api_ok({"analysis": serialize_analysis(analysis, include_detail=True)})
