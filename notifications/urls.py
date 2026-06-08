from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("api/", views.api_inbox, name="api_inbox"),
    path("", views.spa, name="inbox"),
]
