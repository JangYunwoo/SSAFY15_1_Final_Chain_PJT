from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Post


@login_required
def list_posts(request):
    posts = Post.objects.select_related("author", "analysis")
    return render(request, "community/list.html", {"posts": posts})


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("community:detail", pk=post.pk)
    else:
        form = PostForm()
    return render(request, "community/form.html", {"form": form})


@login_required
def detail(request, pk):
    post = get_object_or_404(Post.objects.select_related("analysis", "author"), pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect("community:detail", pk=post.pk)
    else:
        form = CommentForm()
    return render(request, "community/detail.html", {"post": post, "form": form})
