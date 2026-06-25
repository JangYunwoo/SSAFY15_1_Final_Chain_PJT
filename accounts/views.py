from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from api_utils import api_error, api_ok, form_errors, json_body
from .forms import ProfileForm, UserRegisterForm
from .models import User


LINE_ROLE_LABELS = {
    "owner": "담당자",
    "reviewer": "책임자",
}


def spa(request, *args, **kwargs):
    return render(request, "base.html")


def lot_assignment_role_label(user):
    if user.is_staff:
        return "관리자"

    roles = [
        LINE_ROLE_LABELS.get(role, role)
        for role in user.line_assignments.order_by("role").values_list("role", flat=True).distinct()
    ]
    return ", ".join(roles) if roles else "미정"


def lot_assignment_role_key(user):
    if user.is_staff:
        return "admin"
    roles = set(user.line_assignments.values_list("role", flat=True))
    if "reviewer" in roles:
        return "responsible"
    if "owner" in roles:
        return "owner"
    return "unassigned"


def user_role_sort_key(user):
    order = {
        "admin": 0,
        "responsible": 1,
        "owner": 2,
        "unassigned": 3,
    }
    return (order.get(lot_assignment_role_key(user), 9), user.display_name().lower(), user.username.lower())


class WaferLogoutView(LogoutView):
    http_method_names = ["get", "post", "options"]
    next_page = "http://127.0.0.1:5173/"
    success_url_allowed_hosts = {"127.0.0.1:5173", "localhost:5173"}

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


def serialize_user(user):
    profile_image_url = user.profile_image.url if user.profile_image else ""
    line_role = lot_assignment_role_label(user)
    line_role_key = lot_assignment_role_key(user)
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "displayName": user.display_name(),
        "email": user.email,
        "department": user.department,
        "title": user.title,
        "phone": user.phone,
        "profileImageUrl": profile_image_url,
        "role": user.role,
        "isStaff": user.is_staff,
        "lineRole": line_role,
        "lineRoleKey": line_role_key,
        "lotRole": line_role,
        "lotRoleKey": line_role_key,
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
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
    else:
        form = ProfileForm(json_body(request), instance=request.user)
    if not form.is_valid():
        return api_error("프로필 정보를 확인해주세요.", errors=form_errors(form))
    form.save()
    return api_ok({"user": serialize_user(request.user)})


@login_required
def api_users(request):
    users = sorted(
        User.objects.filter(is_active=True),
        key=user_role_sort_key,
    )
    return api_ok({
        "users": [
            {
                "id": user.id,
                "displayName": user.display_name(),
                "email": user.email,
                "department": user.department,
                "title": user.title,
                "profileImageUrl": user.profile_image.url if user.profile_image else "",
                "role": user.role,
                "isStaff": user.is_staff,
                "lineRole": lot_assignment_role_label(user),
                "lineRoleKey": lot_assignment_role_key(user),
                "lotRole": lot_assignment_role_label(user),
                "lotRoleKey": lot_assignment_role_key(user),
            }
            for user in users
        ]
    })


@login_required
def api_user_detail(request, pk):
    user = get_object_or_404(User.objects.filter(is_active=True), pk=pk)
    if user.pk == request.user.pk:
        return api_ok({"user": serialize_user(user)})
    return api_ok({
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "displayName": user.display_name(),
            "email": user.email,
            "department": user.department,
            "title": user.title,
            "phone": user.phone,
            "profileImageUrl": user.profile_image.url if user.profile_image else "",
            "role": user.role,
            "isStaff": user.is_staff,
            "lineRole": lot_assignment_role_label(user),
            "lineRoleKey": lot_assignment_role_key(user),
            "lotRole": lot_assignment_role_label(user),
            "lotRoleKey": lot_assignment_role_key(user),
        }
    })
