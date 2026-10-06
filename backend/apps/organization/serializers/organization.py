from rest_framework import serializers

from apps.organization.models import Organization
from apps.users.serializers import UserDetailSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    owner = UserDetailSerializer(read_only=True)
    members = UserDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = "__all__"
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
