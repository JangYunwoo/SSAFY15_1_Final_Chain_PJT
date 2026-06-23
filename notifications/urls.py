from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("api/", views.api_inbox, name="api_inbox"),
    path("api/notifications/<int:pk>/read/", views.api_mark_notification_read, name="api_notification_read"),
    path("api/notifications/read-all/", views.api_mark_all_notifications_read, name="api_notifications_read_all"),
    path("api/mails/<int:pk>/read/", views.api_mark_mail_read, name="api_mail_read"),
    path("api/mails/<int:pk>/favorite/", views.api_toggle_mail_favorite, name="api_mail_favorite"),
    path("", views.spa, name="inbox"),
]
