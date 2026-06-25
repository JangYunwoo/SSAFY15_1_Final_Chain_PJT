from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification

from .models import AnalysisBatch, LineAssignment


@receiver(post_save, sender=LineAssignment)
def notify_line_assignment(sender, instance, created, **kwargs):
    if not created:
        return

    latest_batch = AnalysisBatch.objects.filter(lot__line=instance.line).order_by("-created_at").first()
    target_url = f"/analyses/history/?batch={latest_batch.id}" if latest_batch else "/analyses/history/"
    Notification.objects.create(
        user=instance.user,
        type="lot_assignment",
        title=f"Line {instance.line.name or instance.line.line_id} 배정",
        body=f"Line {instance.line.name or instance.line.line_id}에서 발생한 LOT 분석 결과를 확인할 수 있습니다.",
        batch=latest_batch,
        target_url=target_url,
    )
