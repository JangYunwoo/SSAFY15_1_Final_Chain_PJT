from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api_utils import api_ok, serialize_datetime
from .models import Mail, Notification


@login_required
def spa(request):
    return render(request, "base.html")


@login_required
def api_inbox(request):
    notifications = Notification.objects.filter(user=request.user)
    mails = Mail.objects.filter(receiver=request.user).select_related("sender")
    return api_ok({
        "notifications": [
            {
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "body": item.body,
                "isRead": item.is_read,
                "isFavorite": item.is_favorite,
                "analysisId": item.analysis_id,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in notifications
        ],
        "mails": [
            {
                "id": item.id,
                "sender": item.sender.display_name(),
                "subject": item.subject,
                "body": item.body,
                "isRead": item.is_read,
                "analysisId": item.analysis_id,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in mails
        ],
    })
