from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST

from api_utils import api_error, api_ok, json_body, serialize_datetime
from .models import Mail, Notification


@login_required
def spa(request):
    return render(request, "base.html")


def serialize_mail(mail):
    return {
        "id": mail.id,
        "sender": mail.sender.display_name(),
        "subject": mail.subject,
        "body": mail.body,
        "isRead": mail.is_read,
        "isFavorite": mail.is_favorite,
        "analysisId": mail.analysis_id,
        "createdAt": serialize_datetime(mail.created_at),
    }


def serialize_recipient(user):
    return {
        "id": user.id,
        "displayName": user.display_name(),
        "email": user.email,
        "department": user.department,
    }


@login_required
def api_inbox(request):
    User = get_user_model()
    notifications = Notification.objects.filter(user=request.user)
    mails = Mail.objects.filter(receiver=request.user).select_related("sender")
    recipients = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by("name", "username")
    return api_ok({
        "notifications": [
            {
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "body": item.body,
                "isRead": item.is_read,
                "analysisId": item.analysis_id,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in notifications
        ],
        "mails": [
            serialize_mail(item)
            for item in mails
        ],
        "users": [serialize_recipient(user) for user in recipients],
    })


@login_required
@require_http_methods(["GET", "DELETE"])
def api_mail_detail(request, pk):
    mail = get_object_or_404(
        Mail.objects.select_related("sender", "receiver").filter(receiver=request.user),
        pk=pk,
    )
    if request.method == "DELETE":
        mail.delete()
        return api_ok()

    if not mail.is_read:
        mail.is_read = True
        mail.save(update_fields=["is_read"])
    return api_ok({"mail": serialize_mail(mail)})


@login_required
@require_POST
def api_send_mail(request):
    data = json_body(request)
    receiver_id = data.get("receiverId")
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()

    if not receiver_id or not subject or not body:
        return api_error("받는 사람, 제목, 내용을 모두 입력해주세요.")

    User = get_user_model()
    try:
        receiver = User.objects.get(id=receiver_id, is_active=True)
    except User.DoesNotExist:
        return api_error("받는 사람을 찾을 수 없습니다.", status=404)

    if receiver.id == request.user.id:
        return api_error("자기 자신에게는 메일을 보낼 수 없습니다.")

    mail = Mail.objects.create(
        sender=request.user,
        receiver=receiver,
        subject=subject,
        body=body,
    )
    return api_ok({"mail": serialize_mail(mail)}, status=201)
