from django.urls import path

from . import views

app_name = "analyses"

urlpatterns = [
    path("api/lots/", views.api_lots, name="api_lots"),
    path("api/lot-assignments/", views.api_lot_assignments, name="api_lot_assignments"),
    path("api/lot-assignments/<int:pk>/", views.api_lot_assignment_detail, name="api_lot_assignment_detail"),
    path("api/upload/", views.api_upload, name="api_upload"),
    path("api/history/", views.api_history, name="api_history"),
    path("api/batches/<int:pk>/", views.api_batch_detail, name="api_batch_detail"),
    path("api/batches/<int:pk>/favorite/", views.api_toggle_batch_favorite, name="api_toggle_batch_favorite"),
    path("api/batches/<int:pk>/insights/", views.api_create_batch_insight, name="api_create_batch_insight"),
    path("api/custom-analyses/", views.api_create_custom_analysis, name="api_create_custom_analysis"),
    path("api/custom-analyses/<int:pk>/favorite/", views.api_toggle_custom_analysis_favorite, name="api_toggle_custom_analysis_favorite"),
    path("api/<int:pk>/", views.api_detail, name="api_detail"),
    path("upload/", views.spa, name="upload"),
    path("history/", views.spa, name="history"),
    path("batches/<int:pk>/", views.spa, name="batch_detail"),
    path("<int:pk>/", views.spa, name="detail"),
    path("<int:pk>/recommendations/", views.spa, name="recommendations"),
]
