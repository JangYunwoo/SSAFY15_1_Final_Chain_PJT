from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from api_utils import api_ok
from analyses.views import serialize_analysis, serialize_batch
from analyses.models import AnalysisBatch, Line, Lot, WaferAnalysis


@login_required
def spa(request):
    return render(request, "base.html")


@login_required
def api_home(request):
    if request.user.is_staff:
        analyses = WaferAnalysis.objects.select_related("lot", "batch", "user")
        batches = AnalysisBatch.objects.select_related("lot")[:5]
        lots = Lot.objects.all()
        lines = Line.objects.all()
        batch_count = AnalysisBatch.objects.count()
    else:
        lines = Line.objects.filter(assignments__user=request.user).distinct()
        lots = Lot.objects.filter(line__in=lines).distinct()
        analyses = WaferAnalysis.objects.filter(lot__in=lots).select_related("lot", "batch", "user")
        batches = AnalysisBatch.objects.filter(lot__in=lots).select_related("lot")[:5]
        batch_count = AnalysisBatch.objects.filter(lot__in=lots).count()
    sample = list(analyses.filter(status=WaferAnalysis.STATUS_DONE)[:100])
    trend_counts = {}
    normal_count = 0
    for item in sample:
        is_normal = item.effective_yield_rate is not None and item.effective_yield_rate >= 90
        label = "Normal" if is_normal else item.predicted_label or "미분류"
        trend_counts[label] = trend_counts.get(label, 0) + 1
        normal_count += int(is_normal)
    trend_distribution = [
        {"label": label, "count": count, "percent": round(count / len(sample) * 100, 1)}
        for label, count in sorted(trend_counts.items(), key=lambda item: item[1], reverse=True)
    ]
    top_label = analyses.values("predicted_label").annotate(total=Count("id")).order_by("-total").first()
    return api_ok({
        "metrics": {
            "lineCount": lines.count(),
            "lineIds": [] if request.user.is_staff else list(lines.order_by("line_id").values_list("line_id", flat=True)),
            "lotCount": lots.count(),
            "lotIds": [] if request.user.is_staff else list(lots.order_by("lot_id").values_list("lot_id", flat=True)),
            "batchCount": batch_count,
            "analysisCount": analyses.count(),
            "lowConfidenceCount": sum(1 for item in sample if item.is_low_confidence),
            "recentNormalRate": round(normal_count / max(len(sample), 1) * 100, 1),
            "topLabel": top_label,
        },
        "recent": [serialize_analysis(item) for item in analyses[:5]],
        "recentTrend": {
            "total": len(sample),
            "normalCount": normal_count,
            "distribution": trend_distribution,
        },
        "recentBatches": [serialize_batch(item) for item in batches],
    })
