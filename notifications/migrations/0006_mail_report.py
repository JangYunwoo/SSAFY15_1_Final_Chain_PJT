from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0005_backfill_notification_batch"),
        ("reports", "0005_move_legacy_body_to_ai_body"),
    ]

    operations = [
        migrations.AddField(
            model_name="mail",
            name="report",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mails",
                to="reports.report",
            ),
        ),
    ]
