from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reports", "0002_report_batch_custom_analysis")]
    operations = [migrations.AddField(model_name="report", name="ai_body", field=models.TextField(blank=True))]
