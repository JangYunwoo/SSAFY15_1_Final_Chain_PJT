from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_POST

from api_utils import api_error, api_ok, serialize_datetime
from .models import Mail, Notification


@login_required
def spa(request):
    return render(request, "base.html")


@login_required
def api_inbox(request):
    notifications = Notification.objects.filter(user=request.user)
    mails = Mail.objects.filter(receiver=request.user).select_related("sender")
    sent_mails = Mail.objects.filter(sender=request.user).select_related("receiver")
    return api_ok({
        "notifications": [
            {
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "body": item.body,
                "isRead": item.is_read,
                "analysisId": item.analysis_id,
                "batchId": item.batch_id,
                "targetUrl": item.target_url or (f"/analyses/history/?batch={item.batch_id}" if item.batch_id else f"/analyses/{item.analysis_id}/" if item.analysis_id else "/notifications/"),
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
                "isFavorite": item.is_favorite,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in mails
        ],
        "sentMails": [
            {
                "id": item.id,
                "receiver": item.receiver.display_name(),
                "subject": item.subject,
                "body": item.body,
                "isRead": item.is_read,
                "isFavorite": item.is_favorite,
                "analysisId": item.analysis_id,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in sent_mails
        ],
    })


@login_required
@require_POST
def api_mark_notification_read(request, pk):
    updated = Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    if not updated:
        return api_error("알림을 찾을 수 없습니다.", status=404)
    return api_ok()


@login_required
@require_POST
def api_mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return api_ok()


@login_required
@require_POST
def api_mark_mail_read(request, pk):
    updated = Mail.objects.filter(pk=pk, receiver=request.user).update(is_read=True)
    if not updated:
        return api_error("메일을 찾을 수 없습니다.", status=404)
    return api_ok()


@login_required
@require_POST
def api_toggle_mail_favorite(request, pk):
    mail = Mail.objects.filter(pk=pk, receiver=request.user).first()
    if not mail:
        return api_error("메일을 찾을 수 없습니다.", status=404)
    mail.is_favorite = not mail.is_favorite
    mail.save(update_fields=["is_favorite"])
    return api_ok({"isFavorite": mail.is_favorite})
