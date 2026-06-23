from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0003_waferanalysis_probabilities_json"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BatchInsight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("label_distribution", models.JSONField(default=dict)),
                ("recommendation_text", models.TextField(blank=True)),
                ("recommendations_json", models.JSONField(default=list)),
                ("report_body", models.TextField(blank=True)),
                ("is_custom", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("analyses", models.ManyToManyField(blank=True, related_name="batch_insights", to="analyses.waferanalysis")),
                ("batch", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="insights", to="analyses.analysisbatch")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="batch_insights", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
