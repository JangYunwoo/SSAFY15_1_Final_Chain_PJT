from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from api_utils import api_ok
from analyses.views import serialize_analysis, serialize_batch
from analyses.models import AnalysisBatch, Lot, WaferAnalysis


@login_required
def spa(request):
    return render(request, "base.html")


@login_required
def api_home(request):
    if request.user.is_staff:
        analyses = WaferAnalysis.objects.select_related("lot", "batch", "user")
        batches = AnalysisBatch.objects.select_related("lot")[:5]
        lots = Lot.objects.all()
        batch_count = AnalysisBatch.objects.count()
    else:
        lots = Lot.objects.filter(assignments__user=request.user).distinct()
        analyses = WaferAnalysis.objects.filter(lot__in=lots).select_related("lot", "batch", "user")
        batches = AnalysisBatch.objects.filter(lot__in=lots).select_related("lot")[:5]
        batch_count = AnalysisBatch.objects.filter(lot__in=lots).count()
    sample = list(analyses[:100])
    avg_confidence = round(sum(float(item.confidence) for item in sample) / max(len(sample), 1) * 100, 1)
    top_label = analyses.values("predicted_label").annotate(total=Count("id")).order_by("-total").first()
    return api_ok({
        "metrics": {
            "lotCount": lots.count(),
            "batchCount": batch_count,
            "analysisCount": analyses.count(),
            "lowConfidenceCount": sum(1 for item in sample if item.is_low_confidence),
            "avgConfidence": avg_confidence,
            "topLabel": top_label,
        },
        "recent": [serialize_analysis(item) for item in analyses[:5]],
        "recentBatches": [serialize_batch(item) for item in batches],
    })
