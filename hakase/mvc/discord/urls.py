from django.urls import path
from .views import tags, user, save_user

urlpatterns = [
    path("tags", tags),
    path("user", user),
    path("user/save", save_user)
]
