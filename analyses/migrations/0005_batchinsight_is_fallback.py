from django.db import migrations, models


def mark_existing_fallbacks(apps, schema_editor):
    BatchInsight = apps.get_model("analyses", "BatchInsight")
    BatchInsight.objects.filter(recommendation_text__contains="GMS_KEY").update(is_fallback=True)


class Migration(migrations.Migration):
    dependencies = [("analyses", "0004_batchinsight")]
    operations = [
        migrations.AddField(
            model_name="batchinsight",
            name="is_fallback",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_fallbacks, migrations.RunPython.noop),
    ]
