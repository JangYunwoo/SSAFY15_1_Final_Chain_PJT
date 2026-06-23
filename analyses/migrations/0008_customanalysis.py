from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0007_gmsconnectionstate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="CustomAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("label_distribution", models.JSONField(default=dict)),
                ("recommendation_text", models.TextField(blank=True)),
                ("recommendations_json", models.JSONField(default=list)),
                ("report_body", models.TextField(blank=True)),
                ("is_fallback", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("analyses", models.ManyToManyField(related_name="custom_analyses", to="analyses.waferanalysis")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="custom_analyses", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
