from django.contrib.contenttypes.models import ContentType

from apps.comments.models import Comment
from apps.comments.permissions import IsProjectMember
from apps.shared.services import BaseService

APP_LABEL_MAP = {
    "organization": "organization",
    "department": "department",
    "project": "projects",
    "task": "tasks",
}


class GetCommentsService(BaseService):
    def process(self):
        request = self.request
        view = self.view
        queryset = self.queryset

        target_type = request.query_params.get("target_type")
        target_id = request.query_params.get("target_id")
        parent_id = request.query_params.get("parent")

        if parent_id:
            parent_comment = self.get_object_or_none(Comment, id=parent_id)
            if not parent_comment:
                return queryset.none()

            permission = IsProjectMember()
            self.check_permission(
                permission.has_object_permission(request, view, parent_comment),
                "Permission denied for parent comment.",
            )
            return queryset.filter(parent_id=parent_id)

        if target_type and target_id:
            app_label = APP_LABEL_MAP.get(target_type)
            if not app_label:
                return queryset.none()

            ct = self.get_object_or_none(
                ContentType, app_label=app_label, model=target_type
            )
            if not ct:
                return queryset.none()

            target_model = ct.model_class()
            target_obj = self.get_object_or_none(target_model, id=target_id)
            if not target_obj:
                return queryset.none()

            permission = IsProjectMember()
            self.check_permission(
                permission.has_object_permission(request, view, target_obj),
                "Permission denied for target object.",
            )

            return queryset.filter(
                content_type=ct, object_id=target_id, parent__isnull=True
            )

        return queryset.filter(author=request.user, parent__isnull=True)


class CreateCommentService(BaseService):
    def process(self):
        request = self.request
        view = self.view
        serializer = self.serializer

        content_type = serializer.validated_data.get("content_type")
        target_id = serializer.validated_data.get("target_id")

        target_model = content_type.model_class()
        target_obj = self.get_object(target_model, id=target_id)

        permission = IsProjectMember()
        self.check_permission(
            permission.has_object_permission(request, view, target_obj),
            "Permission denied for target object.",
        )

        return serializer.save(
            author=request.user, content_type=content_type, object_id=target_id
        )
