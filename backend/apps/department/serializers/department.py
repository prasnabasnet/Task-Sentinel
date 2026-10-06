from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers

from apps.department.models import Department
from apps.users.serializers import UserDetailSerializer

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    head = UserDetailSerializer(read_only=True)
    head_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="head",
        write_only=True,
        required=False,
        allow_null=True,
    )
    member_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "head",
            "head_id",
            "member_count",
            "project_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "member_count",
            "project_count",
            "created_at",
            "updated_at",
        ]
        validators = []

    def validate(self, attrs):
        view = self.context.get("view")
        if view and hasattr(view, "kwargs"):
            oid = view.kwargs.get("oid")
            name = attrs.get("name")
            if oid and name:
                qs = Department.objects.filter(organization_id=oid, name=name)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError(
                        {
                            "name": "A department with this name already exists in this organization."
                        }
                    )
        return attrs

    def get_member_count(self, obj):
        direct_members = set(obj.members.values_list("id", flat=True))
        if obj.head_id:
            direct_members.add(obj.head_id)
        project_members = set(
            User.objects.filter(
                models.Q(project_memberships__project__department=obj)
                | models.Q(assigned_tasks__project__department=obj)
            ).values_list("id", flat=True)
        )
        return len(direct_members.union(project_members))

    def get_project_count(self, obj):
        return obj.projects.count()
