from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("", views.list_posts, name="list"),
    path("new/", views.create_post, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
]
