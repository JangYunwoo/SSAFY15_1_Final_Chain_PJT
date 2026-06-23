from django.db import migrations, models


def open_circuit_when_prior_fallbacks_exist(apps, schema_editor):
    BatchInsight = apps.get_model("analyses", "BatchInsight")
    GmsConnectionState = apps.get_model("analyses", "GmsConnectionState")
    has_failures = BatchInsight.objects.filter(is_fallback=True).exists()
    GmsConnectionState.objects.get_or_create(
        pk=1,
        defaults={
            "is_circuit_open": has_failures,
            "failure_count": 1 if has_failures else 0,
            "last_error": "Previous GMS response transport failure" if has_failures else "",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("analyses", "0006_mark_fallback_insights")]
    operations = [
        migrations.CreateModel(
            name="GmsConnectionState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_circuit_open", models.BooleanField(default=False)),
                ("failure_count", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(open_circuit_when_prior_fallbacks_exist, migrations.RunPython.noop),
    ]
