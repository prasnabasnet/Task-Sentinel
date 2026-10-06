from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.department.models import Department
from apps.projects.models import Project

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "department",
            "member_count",
            "task_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_owner(self, obj):
        return {
            "id": obj.owner.id,
            "email": obj.owner.email,
            "role": obj.owner.role,
        }

    def get_member_count(self, obj):
        return getattr(obj, "member_count", obj.members.count())

    def get_task_count(self, obj):
        return getattr(obj, "task_count", 0)

    def validate_department(self, value):
        user = self.context.get("request") and self.context["request"].user
        if not user:
            return value
        if getattr(user, "is_admin", False) or getattr(user, "role", "") == "ADMIN":
            return value

        org = value.organization
        is_owner = org.owner_id == user.id
        is_org_member = (
            org.memberships.filter(user=user).exists()
            or org.departments.filter(head=user).exists()
            or org.departments.filter(members=user).exists()
            or org.departments.filter(projects__members=user).exists()
            or org.departments.filter(projects__tasks__assignees=user).exists()
        )
        if not (is_owner or is_org_member):
            raise serializers.ValidationError(
                "You must belong to the organization of this department to create/assign a project in it."
            )
        return value
