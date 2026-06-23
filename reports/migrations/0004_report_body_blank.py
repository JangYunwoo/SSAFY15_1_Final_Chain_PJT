from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reports", "0003_report_ai_body")]
    operations = [migrations.AlterField(model_name="report", name="body", field=models.TextField(blank=True))]
