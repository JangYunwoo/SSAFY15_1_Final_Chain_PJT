from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0002_lot_waferanalysis_die_size_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="waferanalysis",
            name="probabilities_json",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
