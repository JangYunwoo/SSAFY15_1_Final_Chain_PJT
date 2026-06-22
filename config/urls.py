from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from notifications import views as notification_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("analyses/", include("analyses.urls")),
    path("community/", include("community.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
    path("mails/<int:pk>/", notification_views.spa, name="mail_detail"),
    path("mails/", notification_views.spa, name="mails"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
