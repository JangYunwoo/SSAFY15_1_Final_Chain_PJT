from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_POST

from api_utils import api_error, api_ok, json_body, serialize_datetime
from reports.models import Report

from .models import Mail, Notification


@login_required
def spa(request):
    return render(request, "base.html")


def report_lot_ids(report):
    lot_ids = set()
    if report.analysis_id and report.analysis and report.analysis.lot_id:
        lot_ids.add(report.analysis.lot_id)
    if report.batch_id and report.batch:
        lot_ids.add(report.batch.lot_id)
    if report.custom_analysis_id and report.custom_analysis:
        lot_ids.update(
            report.custom_analysis.analyses.exclude(lot_id__isnull=True).values_list("lot_id", flat=True)
        )
    return lot_ids


def can_attach_report(user, report):
    if user.is_staff or report.author_id == user.id:
        return True
    if not report.is_shared_to_community:
        return False

    lot_ids = report_lot_ids(report)
    if not lot_ids:
        return False
    assigned_lot_ids = set(user.lot_assignments.values_list("lot_id", flat=True))
    return lot_ids.issubset(assigned_lot_ids)


def attachable_reports(user):
    reports = Report.objects.select_related(
        "analysis__lot",
        "batch__lot",
        "custom_analysis",
        "author",
    ).prefetch_related("custom_analysis__analyses__lot")
    return [report for report in reports if can_attach_report(user, report)]


def serialize_attached_report(report):
    if not report:
        return None
    source_type = "analysis" if report.analysis_id else "batch" if report.batch_id else "custom"
    source_id = report.analysis_id or report.batch_id or report.custom_analysis_id
    return {
        "id": report.id,
        "title": report.title,
        "sourceType": source_type,
        "sourceId": source_id,
        "author": report.author.display_name(),
        "aiBody": report.ai_body,
        "body": report.body,
        "createdAt": serialize_datetime(report.created_at),
    }


def serialize_report_option(report):
    source_type = "분석" if report.analysis_id else "배치" if report.batch_id else "커스텀"
    return {
        "id": report.id,
        "title": report.title,
        "sourceType": source_type,
        "createdAt": serialize_datetime(report.created_at),
    }


def serialize_mail(mail):
    return {
        "id": mail.id,
        "senderId": mail.sender_id,
        "sender": mail.sender.display_name(),
        "receiverId": mail.receiver_id,
        "receiver": mail.receiver.display_name(),
        "subject": mail.subject,
        "body": mail.body,
        "isRead": mail.is_read,
        "isFavorite": mail.is_favorite,
        "analysisId": mail.analysis_id,
        "reportId": mail.report_id,
        "attachedReport": serialize_attached_report(mail.report),
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
    mails = Mail.objects.filter(receiver=request.user).select_related("sender", "receiver", "report__author")
    sent_mails = Mail.objects.filter(sender=request.user).select_related("sender", "receiver", "report__author")
    recipients = User.objects.filter(is_active=True).order_by("name", "username")
    reports = attachable_reports(request.user)
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
                "targetUrl": item.target_url or (
                    f"/analyses/history/?batch={item.batch_id}"
                    if item.batch_id
                    else f"/analyses/{item.analysis_id}/"
                    if item.analysis_id
                    else "/notifications/"
                ),
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in notifications
        ],
        "mails": [serialize_mail(item) for item in mails],
        "sentMails": [serialize_mail(item) for item in sent_mails],
        "users": [serialize_recipient(user) for user in recipients],
        "reports": [serialize_report_option(report) for report in reports],
    })


@login_required
@require_http_methods(["GET", "DELETE"])
def api_mail_detail(request, pk):
    mail = get_object_or_404(
        Mail.objects.select_related("sender", "receiver", "report__author").filter(
            Q(receiver=request.user) | Q(sender=request.user)
        ),
        pk=pk,
    )
    if request.method == "DELETE":
        mail.delete()
        return api_ok()

    if mail.receiver_id == request.user.id and not mail.is_read:
        mail.is_read = True
        mail.save(update_fields=["is_read"])
    return api_ok({"mail": serialize_mail(mail)})


@login_required
@require_POST
def api_read_notification(request, pk):
    notification = get_object_or_404(Notification.objects.filter(user=request.user), pk=pk)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return api_ok()


@login_required
@require_POST
def api_toggle_mail_favorite(request, pk):
    mail = get_object_or_404(
        Mail.objects.select_related("sender", "receiver", "report__author").filter(receiver=request.user),
        pk=pk,
    )
    mail.is_favorite = not mail.is_favorite
    mail.save(update_fields=["is_favorite"])
    return api_ok({"mail": serialize_mail(mail)})


@login_required
@require_POST
def api_send_mail(request):
    data = json_body(request)
    receiver_id = data.get("receiverId")
    report_id = data.get("reportId")
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()

    if not receiver_id or not subject or not body:
        return api_error("받는 사람, 제목, 내용을 모두 입력해주세요.")

    User = get_user_model()
    try:
        receiver = User.objects.get(id=receiver_id, is_active=True)
    except User.DoesNotExist:
        return api_error("받는 사람을 찾을 수 없습니다.", status=404)

    report = None
    if report_id:
        try:
            report_pk = int(report_id)
        except (TypeError, ValueError):
            return api_error("첨부할 보고서를 확인해주세요.")
        report = next((item for item in attachable_reports(request.user) if item.id == report_pk), None)
        if not report:
            return api_error("첨부할 보고서를 찾을 수 없습니다.", status=404)

    mail = Mail.objects.create(
        sender=request.user,
        receiver=receiver,
        subject=subject,
        body=body,
        report=report,
    )
    return api_ok({"mail": serialize_mail(mail)}, status=201)
