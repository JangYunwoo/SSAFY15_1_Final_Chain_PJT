from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from api_utils import api_error, api_ok, form_errors, json_body, serialize_datetime
from analyses.views import accessible_analyses
from community.models import Post

from .forms import ReportForm
from .models import Report


def default_report_body(analysis):
    rec_lines = "\n".join([f"{item.rank}. {item.process}: {item.reason}" for item in analysis.recommendations.all()])
    return f"""분석 ID: {analysis.analysis_code}
예측 결함: {analysis.predicted_label}
신뢰도: {analysis.confidence_percent}%

요약:
{analysis.summary}

추천 공정 우선순위:
{rec_lines}

담당자 의견:
"""


@login_required
def spa(request, *args, **kwargs):
    return render(request, "base.html")


def serialize_report(report):
    return {
        "id": report.id,
        "analysisId": report.analysis_id,
        "analysisCode": report.analysis.analysis_code,
        "author": report.author.display_name(),
        "title": report.title,
        "body": report.body,
        "isSharedToCommunity": report.is_shared_to_community,
        "createdAt": serialize_datetime(report.created_at),
        "updatedAt": serialize_datetime(report.updated_at),
    }


@login_required
def api_report_for_analysis(request, analysis_pk):
    analysis = get_object_or_404(accessible_analyses(request.user), pk=analysis_pk)
    report = Report.objects.filter(analysis=analysis, author=request.user).first()
    if request.method == "GET":
        return api_ok(
            {
                "report": serialize_report(report) if report else None,
                "initial": {
                    "title": f"{analysis.analysis_code} 분석 보고서",
                    "body": default_report_body(analysis),
                },
            }
        )

    form = ReportForm(json_body(request), instance=report)
    if not form.is_valid():
        return api_error("보고서 내용을 확인해주세요.", errors=form_errors(form))
    obj = form.save(commit=False)
    obj.analysis = analysis
    obj.author = request.user
    obj.save()
    return api_ok({"report": serialize_report(obj)}, status=201 if report is None else 200)


@login_required
def api_detail(request, pk):
    report = get_object_or_404(Report.objects.select_related("analysis", "author"), pk=pk, author=request.user)
    return api_ok({"report": serialize_report(report)})


@login_required
@require_POST
def api_share_to_community(request, pk):
    report = get_object_or_404(Report.objects.select_related("analysis"), pk=pk, author=request.user)
    post = Post.objects.create(
        analysis=report.analysis,
        author=request.user,
        title=f"[보고서 공유] {report.title}",
        content=report.body,
        confidence_snapshot=report.analysis.confidence,
    )
    report.is_shared_to_community = True
    report.save(update_fields=["is_shared_to_community"])
    return api_ok({"postId": post.id})
