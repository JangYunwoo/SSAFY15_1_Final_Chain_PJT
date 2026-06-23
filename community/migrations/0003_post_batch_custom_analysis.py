from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyses", "0008_customanalysis"),
        ("community", "0002_post_favorited_by"),
    ]
    operations = [
        migrations.AddField(
            model_name="post",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="posts", to="analyses.analysisbatch"),
        ),
        migrations.AddField(
            model_name="post",
            name="custom_analysis",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="posts", to="analyses.customanalysis"),
        ),
    ]
