from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, ViewSetMixin
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from djoser.permissions import CurrentUserOrAdmin

from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter
from .serializers import (
    FavoriteSerializer, SubscribeSerializer, IngredientSerializer,
    TagSerializer, ReadRecipeSerializer, UserAvatarSerializer, UserSerializer,
    CreateSubscribeSerializer, WriteRecipeSerializer, TokenSerializer
)
from foodgram.models import Ingredient, Tag, Recipe, Tokens
from users.models import Follow


User = get_user_model()


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
    permission_classes = IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    filter_backends = DjangoFilterBackend,
    filterset_class = RecipeFilter
    http_method_names = (
        'get', 'post', 'patch', 'delete', 'head', 'options', 'trace'
    )

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    def list(self, request, *args, **kwargs):
        recipes = self.filter_queryset(self.get_queryset())
        limit = request.query_params.get('limit')
        if limit:
            recipes = recipes[:int(limit)]
        page = self.paginate_queryset(recipes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)


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
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        followings = User.objects.filter(followings__user=request.user)
        limit = request.query_params.get('limit')
        if limit:
            followings = followings[:int(limit)]
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(followings, request)
        serializer = SubscribeSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class SubscribeViewSet(ViewSetMixin, CreateAPIView, DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = CreateSubscribeSerializer
    permission_classes = IsAuthenticated,

    def get_object(self):
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={'id': self.kwargs['user_id']}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        following = self.get_object()
        try:
            Follow.objects.get(
                user=request.user, following=following
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response(
                {'subscribed': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )


class GetLinkView(APIView):
    http_method_names = ['get', 'head', 'options', 'trace']

    def get(self, request, recipe_id):
        recipe_url = request.build_absolute_uri(reverse('recipes-detail', args=[recipe_id]))
        serializer = TokenSerializer(data={'full_url': recipe_url})
        serializer.is_valid(raise_exception=True)
        token = serializer.create(
            validated_data=serializer.validated_data
        )
        return Response(TokenSerializer(token).data, status=status.HTTP_200_OK)
