from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0004_backfill_report_sources")]
    operations = [migrations.AddField(model_name="comment", name="is_deleted", field=models.BooleanField(default=False))]
