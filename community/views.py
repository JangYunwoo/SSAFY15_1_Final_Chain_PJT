from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from api_utils import api_error, api_ok, form_errors, json_body, serialize_datetime, serialize_decimal

from .forms import CommentForm, PostForm
from .models import Post
from analyses.models import Lot
from notifications.models import Notification


@login_required
def spa(request, *args, **kwargs):
    return render(request, "base.html")


def assigned_lot_ids(user):
    return set(Lot.objects.filter(line__assignments__user=user).values_list("id", flat=True))


def post_lot_ids(post):
    lot_ids = set()
    if post.analysis_id and post.analysis and post.analysis.lot_id:
        lot_ids.add(post.analysis.lot_id)
    if post.batch_id and post.batch:
        lot_ids.add(post.batch.lot_id)
    if post.custom_analysis_id and post.custom_analysis:
        lot_ids.update(
            post.custom_analysis.analyses.exclude(lot_id__isnull=True).values_list("lot_id", flat=True)
        )
    return lot_ids


def can_access_post(user, post):
    if user.is_staff:
        return True

    lot_ids = post_lot_ids(post)
    if not lot_ids:
        return post.author_id == user.id
    return lot_ids.issubset(assigned_lot_ids(user))


def accessible_posts(user):
    posts = Post.objects.select_related(
        "author",
        "analysis__lot",
        "batch__lot",
        "custom_analysis",
    ).prefetch_related("custom_analysis__analyses__lot")
    return [post for post in posts if can_access_post(user, post)]


def serialize_shared_wafer(analysis):
    return {
        "id": analysis.id,
        "analysisCode": analysis.analysis_code,
        "waferId": analysis.wafer_id,
        "predictedLabel": analysis.predicted_label,
        "yieldRate": float(analysis.yield_rate) if analysis.yield_rate is not None else None,
        "isNormal": analysis.yield_rate is not None and float(analysis.yield_rate) >= 90,
        "waferImage": analysis.wafer_image.url if analysis.wafer_image else "",
    }


def serialize_shared_analysis(post):
    if post.batch_id:
        batch = post.batch
        created_at = timezone.localtime(batch.created_at)
        return {
            "title": f"{created_at:%Y-%m-%d %H:%M} 분석데이터",
            "meta": f"{batch.uploaded_file.name.rsplit('/', 1)[-1]} · {batch.total_wafers}장 · LOT {batch.lot.lot_id}",
            "wafers": [serialize_shared_wafer(item) for item in batch.wafer_analyses.all()],
        }
    if post.custom_analysis_id:
        custom = post.custom_analysis
        created_at = timezone.localtime(custom.created_at)
        wafers = list(custom.analyses.all())
        return {
            "title": f"{created_at:%Y-%m-%d %H:%M} 커스텀 분석데이터",
            "meta": f"커스텀 선택 · {len(wafers)}장",
            "wafers": [serialize_shared_wafer(item) for item in wafers],
        }
    if post.analysis_id:
        analysis = post.analysis
        created_at = timezone.localtime(analysis.created_at)
        return {
            "title": f"{created_at:%Y-%m-%d %H:%M} 분석데이터",
            "meta": f"웨이퍼 {analysis.wafer_id or analysis.analysis_code} · LOT {analysis.lot.lot_id if analysis.lot_id else '-'}",
            "wafers": [serialize_shared_wafer(analysis)],
        }
    return None


def extract_author_comment(content):
    marker = "[작성자 코멘트]"
    if marker in content:
        return content.split(marker, 1)[1].lstrip("\n")
    return content


def serialize_comment(comment, viewer):
    deleted_text = "삭제된 댓글입니다." if comment.parent_id is None else "삭제된 답글입니다."
    return {
        "id": comment.id,
        "user": comment.user.display_name(),
        "department": comment.user.department,
        "content": deleted_text if comment.is_deleted else comment.content,
        "parentId": comment.parent_id,
        "isDeleted": comment.is_deleted,
        "canDelete": comment.user_id == viewer.id and not comment.is_deleted,
        "createdAt": serialize_datetime(comment.created_at),
    }


def serialize_post(post, include_comments=False, user=None):
    data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "authorComment": extract_author_comment(post.content),
        "author": post.author.display_name(),
        "department": post.author.department,
        "analysisId": post.analysis_id,
        "analysisCode": post.analysis.analysis_code if post.analysis else "",
        "confidenceSnapshot": serialize_decimal(post.confidence_snapshot),
        "createdAt": serialize_datetime(post.created_at),
        "updatedAt": serialize_datetime(post.updated_at),
        "sharedAnalysis": serialize_shared_analysis(post),
        "isFavorite": bool(user and post.favorited_by.filter(pk=user.pk).exists()),
    }
    if include_comments:
        data["comments"] = [serialize_comment(item, user) for item in post.comments.select_related("user")]
    return data


@login_required
def api_list_posts(request):
    return api_ok({"posts": [serialize_post(item, user=request.user) for item in accessible_posts(request.user)]})


@login_required
@require_POST
def api_create_post(request):
    form = PostForm(json_body(request))
    if not form.is_valid():
        return api_error("게시글 내용을 확인해주세요.", errors=form_errors(form))
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return api_ok({"post": serialize_post(post)}, status=201)


@login_required
def api_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related("analysis__lot", "batch__lot", "custom_analysis", "author").prefetch_related(
            "custom_analysis__analyses__lot",
        ),
        pk=pk,
    )
    if not can_access_post(request.user, post):
        return api_error("접근할 수 없는 게시글입니다.", status=404)
    return api_ok({"post": serialize_post(post, include_comments=True, user=request.user)})


@login_required
@require_POST
def api_toggle_favorite(request, pk):
    post = get_object_or_404(
        Post.objects.select_related("analysis__lot", "batch__lot", "custom_analysis").prefetch_related(
            "custom_analysis__analyses__lot",
        ),
        pk=pk,
    )
    if not can_access_post(request.user, post):
        return api_error("접근할 수 없는 게시글입니다.", status=404)
    if post.favorited_by.filter(pk=request.user.pk).exists():
        post.favorited_by.remove(request.user)
        is_favorite = False
    else:
        post.favorited_by.add(request.user)
        is_favorite = True
    return api_ok({"isFavorite": is_favorite})


@login_required
@require_POST
def api_create_comment(request, pk):
    post = get_object_or_404(
        Post.objects.select_related("analysis__lot", "batch__lot", "custom_analysis", "author").prefetch_related(
            "custom_analysis__analyses__lot",
        ),
        pk=pk,
    )
    if not can_access_post(request.user, post):
        return api_error("접근할 수 없는 게시글입니다.", status=404)
    data = json_body(request)
    form = CommentForm(data)
    if not form.is_valid():
        return api_error("댓글 내용을 확인해주세요.", errors=form_errors(form))
    comment = form.save(commit=False)
    comment.post = post
    comment.user = request.user
    parent_id = data.get("parentId")
    notify_user = None
    is_mention_reply = False
    if parent_id:
        parent = get_object_or_404(post.comments, pk=parent_id)
        notify_user = parent.user
        # A reply to a reply stays in the original thread and visibly mentions
        # the person being answered instead of creating an endlessly deep tree.
        if parent.parent_id:
            comment.parent = parent.parent
            comment.content = f"@{parent.user.display_name()} {comment.content}"
            is_mention_reply = True
        else:
            comment.parent = parent
    comment.save()
    if post.author_id != request.user.id:
        Notification.objects.create(
            user=post.author,
            type="comment",
            title="내 보고서에 새 댓글이 달렸습니다.",
            body=f"{request.user.display_name()}님이 '{post.title}'에 댓글을 남겼습니다.",
            target_url=f"/community/{post.id}/",
        )
    if notify_user and notify_user.id != request.user.id and notify_user.id != post.author_id:
        Notification.objects.create(
            user=notify_user,
            type="mention" if is_mention_reply else "reply",
            title="내 답글에 멘션이 달렸습니다." if is_mention_reply else "내 댓글에 답글이 달렸습니다.",
            body=f"{request.user.display_name()}님이 '{post.title}'에서 답글을 남겼습니다.",
            target_url=f"/community/{post.id}/",
        )
    return api_ok(
        {
            "comment": serialize_comment(comment, request.user)
        },
        status=201,
    )


@login_required
@require_http_methods(["DELETE"])
def api_delete_comment(request, post_pk, pk):
    post = get_object_or_404(
        Post.objects.select_related("analysis__lot", "batch__lot", "custom_analysis").prefetch_related(
            "custom_analysis__analyses__lot",
        ),
        pk=post_pk,
    )
    if not can_access_post(request.user, post):
        return api_error("접근할 수 없는 게시글입니다.", status=404)
    comment = get_object_or_404(post.comments, pk=pk, user=request.user)
    direct_replies = post.comments.filter(parent=comment).exists()
    has_later_reply = False
    if comment.parent_id:
        has_later_reply = post.comments.filter(parent_id=comment.parent_id, created_at__gt=comment.created_at).exists()

    if direct_replies or (comment.parent_id and has_later_reply):
        comment.is_deleted = True
        comment.content = ""
        comment.save(update_fields=["is_deleted", "content"])
        return api_ok({"softDeleted": True})

    comment.delete()
    return api_ok({"softDeleted": False})
