from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.WaferLoginView.as_view(), name="login"),
    path("logout/", views.WaferLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
]
