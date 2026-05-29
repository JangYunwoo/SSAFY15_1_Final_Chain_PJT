from django.contrib import admin

from .models import AnalysisBatch, Lot, LotAssignment, ModelVersion, ProcessRecommendation, WaferAnalysis, WaferLabel


class LotAssignmentInline(admin.TabularInline):
    model = LotAssignment
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
    list_display = ("lot_id", "product_code", "process", "status", "started_at", "due_at")
    list_filter = ("status", "process")
    search_fields = ("lot_id", "product_code")
    inlines = [LotAssignmentInline]


@admin.register(AnalysisBatch)
class AnalysisBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_code", "lot", "created_by", "status", "total_wafers", "created_at")
    list_filter = ("status", "lot", "created_at")
    search_fields = ("batch_code", "lot__lot_id", "created_by__username")


admin.site.register(LotAssignment)
admin.site.register(ModelVersion)
admin.site.register(WaferLabel)
