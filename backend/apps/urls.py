from django.urls import include, path

urlpatterns = [
    path("users/", include("apps.users.urls")),
    path("organizations/", include("apps.organization.urls")),
    path("projects/", include("apps.projects.urls")),
    path("tasks/", include("apps.tasks.urls")),
    path("comments/", include("apps.comments.urls")),
    path("organizations/<int:oid>/departments/", include("apps.department.urls")),
]
