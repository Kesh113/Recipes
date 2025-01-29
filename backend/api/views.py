from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, ViewSetMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter
from .serializers import FavoriteSerializer, IngredientSerializer, TagSerializer, RecipeSerializer, UserAvatarSerializer, UserSerializer
from foodgram.models import Ingredient, Tag, Recipe


User = get_user_model()


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = SearchFilter,
    search_fields = '^name',


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = IsAuthenticatedOrReadOnly,
    filter_backends = DjangoFilterBackend,
    filterset_class = RecipeFilter


class FavoriteViewSet(ViewSetMixin, CreateAPIView, DestroyAPIView):
    serializer_class = FavoriteSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# class UsersViewSet(ModelViewSet):
#     serializer_class = UserSerializer
#     queryset = User.objects.all()
#     http_method_names = (
#         'get', 'post', 'put', 'delete', 'head', 'options', 'trace'
#     )
#     # filter_backends = filters.SearchFilter,
#     # search_fields = 'role', 'username'
#     # permission_classes = IsAdmin,
#     pagination_class = PageNumberPagination

#     @action(
#         detail=False,
#         methods=['get'],
#         url_path=settings.USERNAME_RESERVED,
#         permission_classes=(IsAuthenticated,)
#     )
#     def self_profile(self, request):
#         return Response(
#             UserSerializer(request.user).data,
#             status=status.HTTP_200_OK
#         )

#     @action(
#         detail=False,
#         methods=['put', 'delete'],
#         url_path=settings.USERNAME_RESERVED + '/avatar',
#         permission_classes=(IsAuthenticated,)
#     )
#     def self_avatar(self, request):
#         return Response(UserAvatarSerializer(request.user).data)
