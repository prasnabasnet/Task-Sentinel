import django_filters

from apps.projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    owner = django_filters.NumberFilter(field_name="owner__id")
    created_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Project
        fields = ["name", "owner", "created_after", "created_before"]
