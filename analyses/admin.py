from django.contrib import admin

from .models import AnalysisBatch, Line, LineAssignment, Lot, ModelVersion, ProcessRecommendation, WaferAnalysis, WaferLabel


class LineAssignmentInline(admin.TabularInline):
    model = LineAssignment
    fields = ("user", "role", "assigned_by", "assigned_at")
    readonly_fields = ("assigned_by", "assigned_at")
    extra = 0


class ProcessRecommendationInline(admin.TabularInline):
    model = ProcessRecommendation
    extra = 0


@admin.register(WaferAnalysis)
class WaferAnalysisAdmin(admin.ModelAdmin):
    list_display = ("analysis_code", "lot", "wafer_index", "wafer_id", "user", "predicted_label", "confidence", "status", "created_at")
    list_filter = ("status", "predicted_label", "lot", "process", "created_at")
    search_fields = ("analysis_code", "wafer_id", "lot__lot_id", "user__username")
    inlines = [ProcessRecommendationInline]


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("lot_id", "line", "product_code", "process", "status", "started_at", "due_at")
    list_filter = ("status", "process", "line")
    search_fields = ("lot_id", "product_code", "line__line_id", "line__name")


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ("line_id", "name", "assigned_users", "lot_count", "created_at")
    search_fields = ("line_id", "name", "assignments__user__username", "assignments__user__name")
    inlines = [LineAssignmentInline]

    def assigned_users(self, obj):
        users = [assignment.user.display_name() for assignment in obj.assignments.select_related("user")]
        return ", ".join(users) if users else "-"
    assigned_users.short_description = "Assigned line users"

    def lot_count(self, obj):
        return obj.lots.count()
    lot_count.short_description = "LOT count"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, LineAssignment) and instance.assigned_by_id is None:
                instance.assigned_by = request.user
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


@admin.register(AnalysisBatch)
class AnalysisBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_code", "lot", "created_by", "status", "total_wafers", "created_at")
    list_filter = ("status", "lot", "created_at")
    search_fields = ("batch_code", "lot__lot_id", "created_by__username")


@admin.register(LineAssignment)
class LineAssignmentAdmin(admin.ModelAdmin):
    list_display = ("line", "user", "role", "assigned_by", "assigned_at")
    list_filter = ("role", "assigned_at", "line")
    search_fields = ("line__line_id", "line__name", "user__username", "user__name", "assigned_by__username", "assigned_by__name")
    readonly_fields = ("assigned_at",)

    def save_model(self, request, obj, form, change):
        if obj.assigned_by_id is None:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(ModelVersion)
admin.site.register(WaferLabel)
