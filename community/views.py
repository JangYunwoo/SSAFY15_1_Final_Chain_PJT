from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from api_utils import api_error, api_ok, form_errors, json_body, serialize_datetime, serialize_decimal

from .forms import CommentForm, PostForm
from .models import Post


@login_required
def spa(request, *args, **kwargs):
    return render(request, "base.html")


def serialize_post(post, include_comments=False):
    data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author.display_name(),
        "analysisId": post.analysis_id,
        "analysisCode": post.analysis.analysis_code if post.analysis else "",
        "confidenceSnapshot": serialize_decimal(post.confidence_snapshot),
        "createdAt": serialize_datetime(post.created_at),
        "updatedAt": serialize_datetime(post.updated_at),
    }
    if include_comments:
        data["comments"] = [
            {
                "id": item.id,
                "user": item.user.display_name(),
                "content": item.content,
                "createdAt": serialize_datetime(item.created_at),
            }
            for item in post.comments.select_related("user")
        ]
    return data


@login_required
def api_list_posts(request):
    posts = Post.objects.select_related("author", "analysis")
    return api_ok({"posts": [serialize_post(item) for item in posts]})


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
    post = get_object_or_404(Post.objects.select_related("analysis", "author"), pk=pk)
    return api_ok({"post": serialize_post(post, include_comments=True)})


@login_required
@require_POST
def api_create_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(json_body(request))
    if not form.is_valid():
        return api_error("댓글 내용을 확인해주세요.", errors=form_errors(form))
    comment = form.save(commit=False)
    comment.post = post
    comment.user = request.user
    comment.save()
    return api_ok(
        {
            "comment": {
                "id": comment.id,
                "user": comment.user.display_name(),
                "content": comment.content,
                "createdAt": serialize_datetime(comment.created_at),
            }
        },
        status=201,
    )
