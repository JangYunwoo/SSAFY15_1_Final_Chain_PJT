from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("api/dashboard/", views.api_home, name="api_home"),
    path("", views.spa, name="home"),
]
