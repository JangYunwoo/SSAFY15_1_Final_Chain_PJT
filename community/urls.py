from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("api/", views.api_list_posts, name="api_list"),
    path("api/new/", views.api_create_post, name="api_create"),
    path("api/<int:pk>/", views.api_detail, name="api_detail"),
    path("api/<int:pk>/favorite/", views.api_toggle_favorite, name="api_toggle_favorite"),
    path("api/<int:pk>/comments/", views.api_create_comment, name="api_create_comment"),
    path("api/<int:post_pk>/comments/<int:pk>/", views.api_delete_comment, name="api_delete_comment"),
    path("", views.spa, name="list"),
    path("new/", views.spa, name="create"),
    path("<int:pk>/", views.spa, name="detail"),
]
