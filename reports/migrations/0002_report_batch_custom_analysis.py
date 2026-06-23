from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0008_customanalysis"),
        ("reports", "0001_initial"),
    ]
    operations = [
        migrations.AlterField(
            model_name="report",
            name="analysis",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="reports", to="analyses.waferanalysis"),
        ),
        migrations.AddField(
            model_name="report",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="reports", to="analyses.analysisbatch"),
        ),
        migrations.AddField(
            model_name="report",
            name="custom_analysis",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="reports", to="analyses.customanalysis"),
        ),
    ]
