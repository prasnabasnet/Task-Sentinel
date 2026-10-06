from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.tasks.models import Task
from apps.users.serializers import UserDetailSerializer

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    created_by = UserDetailSerializer(read_only=True)
    assignees = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "status",
            "priority",
            "assignees",
            "created_by",
            "due_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["assignees"] = (
            UserDetailSerializer(instance.assignees.all(), many=True).data
        )
        return representation
