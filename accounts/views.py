from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from api_utils import api_error, api_ok, form_errors, json_body
from .forms import ProfileForm, UserRegisterForm


def spa(request, *args, **kwargs):
    return render(request, "base.html")


class WaferLogoutView(LogoutView):
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "displayName": user.display_name(),
        "email": user.email,
        "department": user.department,
        "title": user.title,
        "phone": user.phone,
        "role": user.role,
        "isStaff": user.is_staff,
    }


@ensure_csrf_cookie
def api_me(request):
    if not request.user.is_authenticated:
        return api_ok({"user": None})
    return api_ok({"user": serialize_user(request.user)})


@require_POST
def api_login(request):
    data = json_body(request)
    user = authenticate(request, username=data.get("username", ""), password=data.get("password", ""))
    if user is None:
        return api_error("아이디 또는 비밀번호가 올바르지 않습니다.", status=401)
    login(request, user)
    return api_ok({"user": serialize_user(user)})


@require_POST
def api_logout(request):
    logout(request)
    return api_ok()


@require_POST
def api_register(request):
    data = json_body(request)
    form = UserRegisterForm(data)
    if not form.is_valid():
        return api_error("회원가입 정보를 확인해주세요.", errors=form_errors(form))
    user = form.save()
    login(request, user)
    return api_ok({"user": serialize_user(user)}, status=201)


@login_required
@require_http_methods(["GET", "POST"])
def api_profile(request):
    if request.method == "GET":
        return api_ok({"user": serialize_user(request.user)})
    form = ProfileForm(json_body(request), instance=request.user)
    if not form.is_valid():
        return api_error("프로필 정보를 확인해주세요.", errors=form_errors(form))
    form.save()
    return api_ok({"user": serialize_user(request.user)})
