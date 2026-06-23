from django.conf import settings
from django.db import models

from analyses.models import AnalysisBatch, CustomAnalysis, WaferAnalysis


class Post(models.Model):
    analysis = models.ForeignKey(WaferAnalysis, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    batch = models.ForeignKey(AnalysisBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    custom_analysis = models.ForeignKey(CustomAnalysis, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_posts")
    title = models.CharField(max_length=200)
    content = models.TextField()
    confidence_snapshot = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    favorited_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="favorite_posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
