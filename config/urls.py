from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from analyses import views as analysis_views
from notifications import views as notification_views

admin.site.site_url = "http://127.0.0.1:5173/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("analyses/", include("analyses.urls")),
    path("community/", include("community.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
    path("management/lot-assignments/", analysis_views.spa, name="lot_assignments"),
    path("mails/<int:pk>/", notification_views.spa, name="mail_detail"),
    path("mails/", notification_views.spa, name="mails"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
