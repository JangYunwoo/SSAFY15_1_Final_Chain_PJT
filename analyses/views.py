from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from notifications.models import Notification
from reports.models import Report

from .forms import BatchUploadForm
from .models import AnalysisBatch, ModelVersion, ProcessRecommendation, WaferAnalysis, WaferLabel
from .services.batch_parser import parse_batch_csv
from .services.classifier import predict_wafer_map
from .services.llm_advisor import generate_advice
from .services.recommender import build_summary, recommend_processes
from .services.wafer_renderer import render_wafer_map_png


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


@login_required
def upload(request):
    if request.method == "POST":
        form = BatchUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.batch_code = make_batch_code()
            batch.status = AnalysisBatch.STATUS_PENDING
            batch.save()
            try:
                rows = parse_batch_csv(batch.uploaded_file.path)
                if not rows:
                    raise ValueError("분석할 웨이퍼 행이 없습니다.")

                for row in rows:
                    if row.lot_id and row.lot_id != batch.lot.lot_id:
                        raise ValueError(f"CSV의 LOT({row.lot_id})이 선택한 LOT({batch.lot.lot_id})과 다릅니다.")

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
            return redirect("analyses:batch_detail", pk=batch.pk)
    else:
        form = BatchUploadForm(user=request.user)
    return render(request, "analyses/upload.html", {"form": form})


@login_required
def history(request):
    analyses = accessible_analyses(request.user)
    label = request.GET.get("label")
    if label:
        analyses = analyses.filter(predicted_label=label)
    batches = accessible_batches(request.user)[:20]
    return render(request, "analyses/history.html", {"analyses": analyses, "batches": batches, "labels": WaferLabel.objects.all()})


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(accessible_batches(request.user), pk=pk)
    return render(request, "analyses/batch_detail.html", {"batch": batch})


@login_required
def detail(request, pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=pk)
    report = Report.objects.filter(analysis=analysis, author=request.user).first()
    return render(request, "analyses/detail.html", {"analysis": analysis, "report": report})


@login_required
def recommendation_detail(request, pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=pk)
    return render(request, "analyses/recommendations.html", {"analysis": analysis})


@login_required
def model_performance(request):
    versions = ModelVersion.objects.all()
    label_counts = WaferAnalysis.objects.values("predicted_label").annotate(total=Count("id")).order_by("-total")
    return render(request, "analyses/model_performance.html", {"versions": versions, "label_counts": label_counts})
