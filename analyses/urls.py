from django.urls import path

from . import views

app_name = "analyses"

urlpatterns = [
    path("api/lots/", views.api_lots, name="api_lots"),
    path("api/upload/", views.api_upload, name="api_upload"),
    path("api/history/", views.api_history, name="api_history"),
    path("api/batches/<int:pk>/", views.api_batch_detail, name="api_batch_detail"),
    path("api/<int:pk>/", views.api_detail, name="api_detail"),
    path("upload/", views.spa, name="upload"),
    path("history/", views.spa, name="history"),
    path("batches/<int:pk>/", views.spa, name="batch_detail"),
    path("<int:pk>/", views.spa, name="detail"),
    path("<int:pk>/recommendations/", views.spa, name="recommendations"),
]
