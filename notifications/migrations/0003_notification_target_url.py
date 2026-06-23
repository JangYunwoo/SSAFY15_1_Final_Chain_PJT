from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0002_mail_is_favorite")]
    operations = [migrations.AddField(model_name="notification", name="target_url", field=models.CharField(blank=True, max_length=255))]
