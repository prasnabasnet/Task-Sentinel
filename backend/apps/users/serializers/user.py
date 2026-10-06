from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar_url", "bio", "display_name"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Used only on the /auth/me/ PATCH endpoint. Cannot touch email or password."""

    class Meta:
        model = Profile
        fields = ["avatar_url", "bio", "display_name"]


class UserRegisterSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ["email", "username", "password", "organization_name"]

    def create(self, validated_data):
        validated_data.pop("organization_name", None)
        validated_data["role"] = "ORG_ADMIN"
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "date_joined",
            "is_active",
            "profile",
        ]
        read_only_fields = ["id", "email", "date_joined"]

    def validate_role(self, value):
        request = self.context.get("request")
        req_user = getattr(request, "user", None) if request else None

        if value == "SUPERADMIN":
            if not req_user or (req_user.role != "SUPERADMIN" and not req_user.is_superuser):
                raise serializers.ValidationError("Only a Superadmin can assign the SUPERADMIN role.")
        return value



class UserListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "date_joined", "profile"]
        read_only_fields = ["id", "email", "date_joined"]
