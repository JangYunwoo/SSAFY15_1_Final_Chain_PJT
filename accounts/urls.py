from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("api/me/", views.api_me, name="api_me"),
    path("api/login/", views.api_login, name="api_login"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/profile/", views.api_profile, name="api_profile"),
    path("api/users/", views.api_users, name="api_users"),
    path("api/users/<int:pk>/", views.api_user_detail, name="api_user_detail"),
    path("login/", views.spa, name="login"),
    path("logout/", views.WaferLogoutView.as_view(), name="logout"),
    path("register/", views.spa, name="register"),
    path("profile/", views.spa, name="profile"),
    path("users/", views.spa, name="users"),
    path("users/<int:pk>/", views.spa, name="user_detail"),
]
