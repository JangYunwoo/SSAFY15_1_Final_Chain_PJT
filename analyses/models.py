from django.conf import settings
from django.db import models


class Lot(models.Model):
    STATUS_READY = "ready"
    STATUS_RUNNING = "running"
    STATUS_HOLD = "hold"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_READY, "대기"),
        (STATUS_RUNNING, "진행"),
        (STATUS_HOLD, "보류"),
        (STATUS_DONE, "완료"),
    ]

    lot_id = models.CharField(max_length=80, unique=True)
    product_code = models.CharField(max_length=80, blank=True)
    process = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_READY)
    started_at = models.DateTimeField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["lot_id"]

    def __str__(self):
        return self.lot_id


class LotAssignment(models.Model):
    ROLE_OWNER = "owner"
    ROLE_REVIEWER = "reviewer"
    ROLE_CHOICES = [
        (ROLE_OWNER, "담당자"),
        (ROLE_REVIEWER, "책임자"),
    ]

    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lot_assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_lot_assignments",
        blank=True,
        null=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_OWNER)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lot", "user")
        ordering = ["lot__lot_id", "user__username"]

    def __str__(self):
        return f"{self.lot.lot_id} - {self.user}"


class AnalysisBatch(models.Model):
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "대기"),
        (STATUS_DONE, "완료"),
        (STATUS_FAILED, "실패"),
    ]

    batch_code = models.CharField(max_length=50, unique=True)
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="analysis_batches")
    uploaded_file = models.FileField(upload_to="wafer/batches/")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analysis_batches")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_wafers = models.PositiveIntegerField(default=0)
    failed_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.batch_code

    @property
    def low_confidence_count(self):
        return sum(1 for item in self.wafer_analyses.all() if item.is_low_confidence)


class WaferAnalysis(models.Model):
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "대기"),
        (STATUS_DONE, "완료"),
        (STATUS_FAILED, "실패"),
    ]

    analysis_code = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wafer_analyses")
    batch = models.ForeignKey(AnalysisBatch, on_delete=models.CASCADE, related_name="wafer_analyses", blank=True, null=True)
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="wafer_analyses", blank=True, null=True)
    uploaded_file = models.FileField(upload_to="wafer/uploads/")
    wafer_image = models.ImageField(upload_to="wafer/images/", blank=True, null=True)
    wafer_id = models.CharField(max_length=80, blank=True)
    wafer_index = models.PositiveIntegerField(blank=True, null=True)
    process = models.CharField(max_length=50, blank=True)
    step = models.CharField(max_length=80, blank=True)
    equipment_id = models.CharField(max_length=80, blank=True)
    recipe_id = models.CharField(max_length=80, blank=True)
    inspection_time = models.DateTimeField(blank=True, null=True)
    die_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    yield_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=90)
    yield_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    wafer_map_json = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    predicted_label = models.CharField(max_length=50, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    probabilities_json = models.JSONField(blank=True, null=True)
    result_csv = models.FileField(upload_to="wafer/results/", blank=True, null=True)
    model_version = models.CharField(max_length=50, default="resnet34-v1")
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.analysis_code

    @property
    def confidence_percent(self):
        return round(float(self.confidence) * 100, 1)

    @property
    def effective_yield_rate(self):
        """Use CSV yield when present, otherwise derive it from 1/(1+2)."""
        if self.yield_rate is not None:
            return round(float(self.yield_rate), 2)
        values = [value for row in (self.wafer_map_json or []) for value in row]
        passed = sum(1 for value in values if float(value) == 1.0)
        failed = sum(1 for value in values if float(value) == 2.0)
        total = passed + failed
        return round(passed / total * 100, 2) if total else None

    @property
    def is_low_confidence(self):
        return float(self.confidence) < getattr(settings, "LOW_CONFIDENCE_THRESHOLD", 0.85)


class ProcessRecommendation(models.Model):
    analysis = models.ForeignKey(WaferAnalysis, on_delete=models.CASCADE, related_name="recommendations")
    rank = models.PositiveSmallIntegerField()
    process = models.CharField(max_length=50)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    stop_alert = models.BooleanField(default=False)

    class Meta:
        ordering = ["rank"]
        unique_together = ("analysis", "rank")


class BatchInsight(models.Model):
    """CSV 배치 또는 선택한 웨이퍼 묶음에 대한 분석 결과."""

    batch = models.ForeignKey(AnalysisBatch, on_delete=models.CASCADE, related_name="insights")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="batch_insights")
    analyses = models.ManyToManyField(WaferAnalysis, related_name="batch_insights", blank=True)
    title = models.CharField(max_length=200)
    label_distribution = models.JSONField(default=dict)
    recommendation_text = models.TextField(blank=True)
    recommendations_json = models.JSONField(default=list)
    report_body = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)
    is_fallback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class GmsConnectionState(models.Model):
    """Stops repeated paid GMS calls while its gateway is unhealthy."""

    is_circuit_open = models.BooleanField(default=False)
    failure_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class CustomAnalysis(models.Model):
    """Analyst-selected wafers across one or more CSV batches."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="custom_analyses")
    title = models.CharField(max_length=200)
    analyses = models.ManyToManyField(WaferAnalysis, related_name="custom_analyses")
    label_distribution = models.JSONField(default=dict)
    recommendation_text = models.TextField(blank=True)
    recommendations_json = models.JSONField(default=list)
    report_body = models.TextField(blank=True)
    is_fallback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ModelVersion(models.Model):
    model_name = models.CharField(max_length=100, default="WaferClassifier")
    version = models.CharField(max_length=30)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4)
    registered_at = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-registered_at"]


class WaferLabel(models.Model):
    label = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    sample_image = models.ImageField(upload_to="wafer/labels/", blank=True, null=True)

    def __str__(self):
        return self.label
