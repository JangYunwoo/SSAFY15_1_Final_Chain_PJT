from django.conf import settings
from django.db import models

from analyses.models import AnalysisBatch, WaferAnalysis


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20)
    title = models.TextField()
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    analysis = models.ForeignKey(WaferAnalysis, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(AnalysisBatch, on_delete=models.SET_NULL, null=True, blank=True)
    target_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Mail(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_mails")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_mails")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    analysis = models.ForeignKey(WaferAnalysis, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
