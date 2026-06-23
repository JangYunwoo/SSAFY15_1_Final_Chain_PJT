from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0008_customanalysis"),
        ("notifications", "0003_notification_target_url"),
    ]
    operations = [
        migrations.AddField(
            model_name="notification",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to="analyses.analysisbatch"),
        ),
    ]
