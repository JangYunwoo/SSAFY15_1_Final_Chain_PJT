from django.urls import path

from . import views

app_name = "analyses"

urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("history/", views.history, name="history"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/recommendations/", views.recommendation_detail, name="recommendations"),
    path("model/performance/", views.model_performance, name="model_performance"),
]
