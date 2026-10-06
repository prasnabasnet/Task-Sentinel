from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.comments.views import CommentViewSet

router = DefaultRouter()
router.register(r"", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
]

