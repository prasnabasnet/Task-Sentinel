from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.comments.models import Comment
from apps.users.serializers import UserDetailSerializer


class ReplySerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    mentions = UserDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "body",
            "mentions",
            "parent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "mentions", "created_at", "updated_at"]


class CommentSerializer(serializers.ModelSerializer):
    target_type = serializers.ChoiceField(
        choices=["organization", "department", "project", "task"], write_only=True, required=False
    )
    target_id = serializers.IntegerField(write_only=True, required=False)

    author = UserDetailSerializer(read_only=True)
    mentions = UserDetailSerializer(many=True, read_only=True)
    replies = ReplySerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "body",
            "mentions",
            "parent",
            "replies",
            "target_type",
            "target_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "mentions"]

    def validate_body(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Comment body cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Comment body cannot exceed 5000 characters."
            )
        return value

    def validate(self, data):
        if self.instance is not None:
            return data

        parent = data.get("parent")
        target_type = data.get("target_type")
        target_id = data.get("target_id")

        if not parent:
            if not target_type or not target_id:
                raise serializers.ValidationError(
                    {
                        "detail": "Root comments must include both 'target_type' and 'target_id'."
                    }
                )

            app_mapping = {
                "organization": "organization",
                "department": "department",
                "project": "projects",
                "task": "tasks",
            }
            app_label = app_mapping.get(target_type)

            try:
                ct = ContentType.objects.get(app_label=app_label, model=target_type)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(
                    {"target_type": "Invalid comment target type."}
                )

            model_class = ct.model_class()
            if not model_class.objects.filter(id=target_id).exists():
                raise serializers.ValidationError(
                    {"target_id": f"No {target_type} found with ID {target_id}."}
                )

            data["content_type"] = ct

        else:
            if target_type or target_id:
                raise serializers.ValidationError(
                    {
                        "detail": "Replies automatically inherit their target. Do not provide target_type or target_id."
                    }
                )

            if parent.parent is not None:
                raise serializers.ValidationError(
                    {
                        "parent": "You cannot reply to a reply. Only 1-level deep threading allowed."
                    }
                )

            data["content_type"] = parent.content_type
            data["target_id"] = parent.object_id

        return data

    def create(self, validated_data):
        validated_data.pop("target_type", None)
        validated_data.pop("target_id", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("target_type", None)
        validated_data.pop("target_id", None)
        return super().update(instance, validated_data)

