from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from analyses.models import AnalysisBatch, Lot, WaferAnalysis


@login_required
def home(request):
    if request.user.is_staff:
        analyses = WaferAnalysis.objects.all()
        batches = AnalysisBatch.objects.select_related("lot")[:5]
        lots = Lot.objects.all()
    else:
        lots = Lot.objects.filter(assignments__user=request.user).distinct()
        analyses = WaferAnalysis.objects.filter(lot__in=lots)
        batches = AnalysisBatch.objects.filter(lot__in=lots).select_related("lot")[:5]
    sample = list(analyses[:100])
    avg_confidence = round(sum(float(a.confidence) for a in sample) / max(len(sample), 1) * 100, 1)
    context = {
        "lot_count": lots.count(),
        "batch_count": AnalysisBatch.objects.filter(lot__in=lots).count() if not request.user.is_staff else AnalysisBatch.objects.count(),
        "analysis_count": analyses.count(),
        "low_confidence_count": sum(1 for item in sample if item.is_low_confidence),
        "avg_confidence": avg_confidence,
        "top_label": analyses.values("predicted_label").annotate(total=Count("id")).order_by("-total").first(),
        "recent": analyses[:5],
        "recent_batches": batches,
    }
    return render(request, "dashboard/home.html", context)
