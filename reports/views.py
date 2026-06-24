from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from api_utils import api_error, api_ok, form_errors, json_body, serialize_datetime
from analyses.models import CustomAnalysis
from analyses.views import accessible_analyses, accessible_batches
from community.models import Post
from notifications.models import Mail

from .forms import ReportForm
from .models import Report


def spa(request, *args, **kwargs):
    return render(request, "base.html")


def default_analysis_body(analysis):
    return f"""분석 ID: {analysis.analysis_code}
예측 결함: {analysis.predicted_label}
신뢰도: {analysis.confidence_percent}%

요약:
{analysis.summary}
"""


def insight_body(source):
    insight = source.insights.order_by("-created_at").first() if hasattr(source, "insights") else None
    if insight:
        return insight.report_body
    return "AI 분석 결과가 아직 없습니다."


def custom_body(custom):
    return custom.report_body or "AI 분석 결과가 아직 없습니다."


def serialize_report(report):
    source_type = "analysis" if report.analysis_id else "batch" if report.batch_id else "custom"
    source_id = report.analysis_id or report.batch_id or report.custom_analysis_id
    return {
        "id": report.id,
        "sourceType": source_type,
        "sourceId": source_id,
        "analysisId": report.analysis_id,
        "analysisCode": report.analysis.analysis_code if report.analysis_id else "",
        "author": report.author.display_name(),
        "title": report.title,
        "aiBody": report.ai_body,
        "body": report.body,
        "isSharedToCommunity": report.is_shared_to_community,
        "createdAt": serialize_datetime(report.created_at),
        "updatedAt": serialize_datetime(report.updated_at),
    }


def report_for_source(request, source, source_type, title, initial_body):
    lookup = {source_type: source}
    report = Report.objects.filter(author=request.user, **lookup).first()
    if request.method == "GET":
        return api_ok({
            "report": serialize_report(report) if report else None,
            "initial": {"title": title, "aiBody": initial_body, "body": ""},
        })

    form = ReportForm(json_body(request), instance=report)
    if not form.is_valid():
        return api_error("보고서 내용을 확인해 주세요.", errors=form_errors(form))
    obj = form.save(commit=False)
    obj.author = request.user
    obj.analysis = source if source_type == "analysis" else None
    obj.batch = source if source_type == "batch" else None
    obj.custom_analysis = source if source_type == "custom_analysis" else None
    obj.ai_body = report.ai_body if report and report.ai_body else initial_body
    obj.save()
    return api_ok({"report": serialize_report(obj)}, status=201 if report is None else 200)


@login_required
def api_report_for_analysis(request, analysis_pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=analysis_pk)
    return report_for_source(request, analysis, "analysis", f"{analysis.analysis_code} 분석 보고서", default_analysis_body(analysis))


@login_required
def api_report_for_batch(request, batch_pk):
    batch = get_object_or_404(accessible_batches(request.user), pk=batch_pk)
    return report_for_source(request, batch, "batch", f"{batch.batch_code} 배치 분석 보고서", insight_body(batch))


@login_required
def api_report_for_custom(request, custom_pk):
    custom = get_object_or_404(CustomAnalysis, pk=custom_pk, user=request.user)
    return report_for_source(request, custom, "custom_analysis", f"{custom.title} 보고서", custom_body(custom))


@login_required
def api_detail(request, pk):
    report = get_object_or_404(Report.objects.select_related("analysis", "batch", "custom_analysis", "author"), pk=pk)
    has_mail_access = Mail.objects.filter(report=report).filter(sender=request.user).exists() or Mail.objects.filter(report=report).filter(receiver=request.user).exists()
    if report.author_id != request.user.id and not request.user.is_staff and not has_mail_access:
        return api_error("접근할 수 없는 보고서입니다.", status=404)
    return api_ok({"report": serialize_report(report)})


@login_required
@require_POST
def api_share_to_community(request, pk):
    report = get_object_or_404(Report.objects.select_related("analysis"), pk=pk, author=request.user)
    Post.objects.create(
        analysis=report.analysis,
        batch=report.batch,
        custom_analysis=report.custom_analysis,
        author=request.user,
        title=f"[보고서 공유] {report.title}",
        content=f"[AI 분석 결과]\n{report.ai_body}\n\n[작성자 코멘트]\n{report.body}",
        confidence_snapshot=report.analysis.confidence if report.analysis_id else 0,
    )
    report.is_shared_to_community = True
    report.save(update_fields=["is_shared_to_community"])
    return api_ok()
