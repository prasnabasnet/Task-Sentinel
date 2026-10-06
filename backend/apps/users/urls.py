from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import LoginView, LogoutView, MemberCreateView, MeView, RegisterView, UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("auth/register/", RegisterView.as_view({"post": "create"}), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("members/", MemberCreateView.as_view(), name="member-create"),
    path("", include(router.urls)),
]

