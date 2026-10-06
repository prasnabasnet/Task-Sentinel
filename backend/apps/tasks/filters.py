import django_filters
from apps.tasks.models.task import Task


class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    due_date_min = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_date_max = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = Task
        fields = [
            "title",
            "due_date_min",
            "due_date_max",
            "project",
            "status",
            "priority",
            "assignees",
        ]
