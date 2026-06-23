from django.db import migrations


def move_legacy_report_body(apps, schema_editor):
    Report = apps.get_model("reports", "Report")
    for report in Report.objects.filter(ai_body="").exclude(body="").iterator():
        report.ai_body = report.body
        report.body = ""
        report.save(update_fields=["ai_body", "body"])


class Migration(migrations.Migration):
    dependencies = [("reports", "0004_report_body_blank")]
    operations = [migrations.RunPython(move_legacy_report_body, migrations.RunPython.noop)]
