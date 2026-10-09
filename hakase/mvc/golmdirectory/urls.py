from django.urls import path
from .views import member_map

urlpatterns = [
    path("", member_map),
]
