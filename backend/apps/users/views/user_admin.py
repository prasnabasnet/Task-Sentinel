from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdmin
from apps.users.serializers import UserDetailSerializer, UserListSerializer
from apps.users.services import DeactivateUserService, GetAllUsersService


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return GetAllUsersService.execute(request=self.request)


    def get_serializer_class(self):
        if self.action in ("retrieve", "partial_update"):
            return UserDetailSerializer
        return UserListSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        DeactivateUserService.execute(user=user)
        return Response(status=status.HTTP_204_NO_CONTENT)
