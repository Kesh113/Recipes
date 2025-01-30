from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, ViewSetMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from djoser.permissions import CurrentUserOrAdmin

from .filters import RecipeFilter
from .serializers import FavoriteSerializer, IngredientSerializer, TagSerializer, RecipeSerializer, UserAvatarSerializer, UserSerializer
from foodgram.models import Ingredient, Tag, Recipe


User = get_user_model()

USER_AVATAR = f'me/avatar'


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = SearchFilter,
    search_fields = '^name',
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = IsAuthenticatedOrReadOnly,
    filter_backends = DjangoFilterBackend,
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteViewSet(ViewSetMixin, CreateAPIView, DestroyAPIView):
    serializer_class = FavoriteSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserViewSet(UserViewSet):
    def get_permissions(self):
        if self.action == 'me' or self.action == 'me_avatar':
            self.permission_classes = CurrentUserOrAdmin,
            return [permission() for permission in self.permission_classes]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
    )
    def me_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
