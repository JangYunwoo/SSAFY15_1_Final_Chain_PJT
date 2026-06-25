from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_lines(apps, schema_editor):
    Line = apps.get_model("analyses", "Line")
    Lot = apps.get_model("analyses", "Lot")
    LotAssignment = apps.get_model("analyses", "LotAssignment")
    LineAssignment = apps.get_model("analyses", "LineAssignment")

    for lot in Lot.objects.all():
        line, _ = Line.objects.get_or_create(
            line_id=lot.lot_id,
            defaults={"name": lot.lot_id},
        )
        lot.line = line
        lot.save(update_fields=["line"])

    for assignment in LotAssignment.objects.select_related("lot"):
        if not assignment.lot.line_id:
            continue
        line_assignment, created = LineAssignment.objects.get_or_create(
            line_id=assignment.lot.line_id,
            user_id=assignment.user_id,
            defaults={
                "role": assignment.role,
                "assigned_by_id": assignment.assigned_by_id,
                "assigned_at": assignment.assigned_at,
            },
        )
        if not created and line_assignment.assigned_by_id is None and assignment.assigned_by_id:
            line_assignment.assigned_by_id = assignment.assigned_by_id
            line_assignment.save(update_fields=["assigned_by"])


def reverse_backfill_lines(apps, schema_editor):
    LineAssignment = apps.get_model("analyses", "LineAssignment")
    LineAssignment.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("analyses", "0009_lotassignment_assigned_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="Line",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_id", models.CharField(max_length=80, unique=True)),
                ("name", models.CharField(blank=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["line_id"],
            },
        ),
        migrations.AddField(
            model_name="lot",
            name="line",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="lots",
                to="analyses.line",
            ),
        ),
        migrations.CreateModel(
            name="LineAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[("owner", "담당자"), ("reviewer", "책임자")],
                        default="owner",
                        max_length=20,
                    ),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_line_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "line",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="analyses.line",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="line_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["line__line_id", "user__username"],
                "unique_together": {("line", "user")},
            },
        ),
        migrations.RunPython(backfill_lines, reverse_backfill_lines),
        migrations.AlterField(
            model_name="lotassignment",
            name="role",
            field=models.CharField(
                choices=[("owner", "담당자"), ("reviewer", "책임자")],
                default="owner",
                max_length=20,
            ),
        ),
    ]
