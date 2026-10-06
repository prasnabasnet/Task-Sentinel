from rest_framework import permissions, viewsets

from apps.comments.models import Comment
from apps.comments.permissions import IsCommentAuthorOrAdmin, IsProjectMember
from apps.comments.serializers import CommentSerializer
from apps.comments.services import CreateCommentService, GetCommentsService


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated, IsProjectMember]

        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes.append(IsCommentAuthorOrAdmin)

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return queryset

        return GetCommentsService.execute(self.request, self, queryset)

    def perform_create(self, serializer):
        CreateCommentService.execute(self.request, self, serializer)
