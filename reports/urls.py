from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("api/analysis/<int:analysis_pk>/", views.api_report_for_analysis, name="api_for_analysis"),
    path("api/batch/<int:batch_pk>/", views.api_report_for_batch, name="api_for_batch"),
    path("api/custom/<int:custom_pk>/", views.api_report_for_custom, name="api_for_custom"),
    path("api/<int:pk>/", views.api_detail, name="api_detail"),
    path("api/<int:pk>/share/", views.api_share_to_community, name="api_share"),
    path("analysis/<int:analysis_pk>/new/", views.spa, name="create_from_analysis"),
    path("batch/<int:batch_pk>/new/", views.spa, name="create_from_batch"),
    path("custom/<int:custom_pk>/new/", views.spa, name="create_from_custom"),
    path("<int:pk>/", views.spa, name="detail"),
]
