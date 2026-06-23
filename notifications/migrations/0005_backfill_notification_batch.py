import re

from django.db import migrations


def backfill_notification_batch(apps, schema_editor):
    Notification = apps.get_model("notifications", "Notification")
    AnalysisBatch = apps.get_model("analyses", "AnalysisBatch")
    for notification in Notification.objects.filter(batch__isnull=True):
        match = re.search(r"BAT\d{8}-\d+", notification.body or "")
        if not match:
            continue
        batch = AnalysisBatch.objects.filter(batch_code=match.group(0)).first()
        if batch:
            notification.batch_id = batch.id
            notification.save(update_fields=["batch"])


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0008_customanalysis"),
        ("notifications", "0004_notification_batch"),
    ]
    operations = [migrations.RunPython(backfill_notification_batch, migrations.RunPython.noop)]
