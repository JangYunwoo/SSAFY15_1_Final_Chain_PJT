from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("analysis/<int:analysis_pk>/new/", views.create_from_analysis, name="create_from_analysis"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/share/", views.share_to_community, name="share"),
]
