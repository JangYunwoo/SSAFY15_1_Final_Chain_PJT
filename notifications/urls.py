from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("api/", views.api_inbox, name="api_inbox"),
    path("api/notifications/<int:pk>/read/", views.api_read_notification, name="api_read_notification"),
    path("api/mails/<int:pk>/", views.api_mail_detail, name="api_mail_detail"),
    path("api/mails/<int:pk>/favorite/", views.api_toggle_mail_favorite, name="api_toggle_mail_favorite"),
    path("api/send/", views.api_send_mail, name="api_send_mail"),
    path("", views.spa, name="inbox"),
]
