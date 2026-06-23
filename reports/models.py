from django.conf import settings
from django.db import models

from analyses.models import AnalysisBatch, CustomAnalysis, WaferAnalysis


class Report(models.Model):
    analysis = models.ForeignKey(WaferAnalysis, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    batch = models.ForeignKey(AnalysisBatch, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    custom_analysis = models.ForeignKey(CustomAnalysis, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=200)
    ai_body = models.TextField(blank=True)
    body = models.TextField(blank=True)
    is_shared_to_community = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
