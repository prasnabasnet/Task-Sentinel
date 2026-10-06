from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.department.views import DepartmentViewSet

router = DefaultRouter()

router.register(r"", DepartmentViewSet, basename="dept")

urlpatterns = [
    path("", include(router.urls)),
] 