from django.db import migrations


def mark_fallbacks_from_recommendations(apps, schema_editor):
    BatchInsight = apps.get_model("analyses", "BatchInsight")
    for insight in BatchInsight.objects.all().iterator():
        recommendations = insight.recommendations_json or []
        is_fallback = any("GMS_KEY" in str(item.get("reason", "")) for item in recommendations if isinstance(item, dict))
        if insight.is_fallback != is_fallback:
            insight.is_fallback = is_fallback
            insight.save(update_fields=["is_fallback"])


class Migration(migrations.Migration):
    dependencies = [("analyses", "0005_batchinsight_is_fallback")]
    operations = [migrations.RunPython(mark_fallbacks_from_recommendations, migrations.RunPython.noop)]
