from django.db import migrations


def backfill_report_sources(apps, schema_editor):
    Post = apps.get_model("community", "Post")
    Report = apps.get_model("reports", "Report")
    for report in Report.objects.filter(is_shared_to_community=True):
        post = Post.objects.filter(
            author_id=report.author_id,
            title=f"[보고서 공유] {report.title}",
            content=report.body,
        ).first()
        if post and not (post.analysis_id or post.batch_id or post.custom_analysis_id):
            post.analysis_id = report.analysis_id
            post.batch_id = report.batch_id
            post.custom_analysis_id = report.custom_analysis_id
            post.save(update_fields=["analysis", "batch", "custom_analysis"])


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0003_post_batch_custom_analysis"),
        ("reports", "0002_report_batch_custom_analysis"),
    ]
    operations = [migrations.RunPython(backfill_report_sources, migrations.RunPython.noop)]
