from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification

from .models import LotAssignment


@receiver(post_save, sender=LotAssignment)
def notify_lot_assignment(sender, instance, created, **kwargs):
    if not created:
        return

    latest_batch = instance.lot.analysis_batches.order_by("-created_at").first()
    target_url = f"/analyses/history/?batch={latest_batch.id}" if latest_batch else "/analyses/history/"
    Notification.objects.create(
        user=instance.user,
        type="lot_assignment",
        title=f"LOT {instance.lot.lot_id} 배정",
        body=f"LOT {instance.lot.lot_id} 분석 결과를 확인할 수 있습니다.",
        batch=latest_batch,
        target_url=target_url,
    )
