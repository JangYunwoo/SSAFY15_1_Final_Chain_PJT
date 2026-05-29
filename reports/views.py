from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from analyses.models import WaferAnalysis
from community.models import Post

from .forms import ReportForm
from .models import Report


def default_report_body(analysis):
    rec_lines = "\n".join([f"{r.rank}. {r.process}: {r.reason}" for r in analysis.recommendations.all()])
    return f"""분석 ID: {analysis.analysis_code}
예측 결함: {analysis.predicted_label}
신뢰도: {analysis.confidence_percent}%

요약:
{analysis.summary}

추천 점검 우선순위:
{rec_lines}

담당자 의견:
"""


@login_required
def create_from_analysis(request, analysis_pk):
    analysis = get_object_or_404(WaferAnalysis, pk=analysis_pk)
    report = Report.objects.filter(analysis=analysis, author=request.user).first()
    if request.method == "POST":
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.analysis = analysis
            obj.author = request.user
            obj.save()
            return redirect("reports:detail", pk=obj.pk)
    else:
        initial = {"title": f"{analysis.analysis_code} 분석 보고서", "body": default_report_body(analysis)}
        form = ReportForm(instance=report, initial=initial)
    return render(request, "reports/form.html", {"form": form, "analysis": analysis})


@login_required
def detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    return render(request, "reports/detail.html", {"report": report})


@login_required
def share_to_community(request, pk):
    report = get_object_or_404(Report, pk=pk)
    post = Post.objects.create(
        analysis=report.analysis,
        author=request.user,
        title=f"[보고서 공유] {report.title}",
        content=report.body,
        confidence_snapshot=report.analysis.confidence,
    )
    report.is_shared_to_community = True
    report.save(update_fields=["is_shared_to_community"])
    return redirect("community:detail", pk=post.pk)
