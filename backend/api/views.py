from django.http import FileResponse
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
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from djoser.permissions import CurrentUserOrAdmin

from .utils import generate_shopping_list
from .permissions import IsAuthorOrReadOnly
from .filters import LimitFilter, RecipeFilter
from .serializers import (
    FavoriteShoppingCartSerializer, SubscribeSerializer, IngredientSerializer,
    TagSerializer, ReadRecipeSerializer, UserAvatarSerializer,
    WriteRecipeSerializer, TokenSerializer
)
from foodgram.models import Favorite, Ingredient, ShoppingCart, Tag, Recipe
from users.models import Subscribe


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)

    @action(['post', 'delete'], detail=True, url_path='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        recipe = self.get_object()
        if request.method == 'POST':
            favorite_recipe, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
            if not created:
                return Response({'favorite': 'Рецепт уже добавлен в избранное'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = FavoriteShoppingCartSerializer(favorite_recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({'favorite': 'Рецепта нет в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True, url_path='shopping_cart', permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        if request.method == 'POST':
            favorite_recipe, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
            if not created:
                return Response({'shopping_car': 'Рецепт уже добавлен в список покупок'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = FavoriteShoppingCartSerializer(favorite_recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({'shopping_car': 'Рецепта нет в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['get'], detail=True, url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe_url = request.build_absolute_uri(reverse('recipes-detail', args=[pk]))
        serializer = TokenSerializer(data={'full_url': recipe_url})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ['get'], detail=False, url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(users_shopping_cart__user=request.user)
        response = FileResponse(
            generate_shopping_list(recipes),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename='shopping_list.txt'
        )
        return response


class FoodgramUserViewSet(UserViewSet):
    http_method_names = (
        'get', 'post', 'put', 'delete', 'head', 'options', 'trace'
    )
    filter_backends = DjangoFilterBackend,
    filterset_class = LimitFilter
    for attr in [
        'activation', 'resend_activation', 'reset_password',
        'reset_password_confirm', 'set_username', 'reset_username',
        'reset_username_confirm'
    ]:
        locals()[attr] = None

    @action(['get'], detail=False, permission_classes=[CurrentUserOrAdmin])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(
        ['put', 'delete'], detail=False, url_path='me/avatar',
        permission_classes=[CurrentUserOrAdmin]
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
        ['get'], detail=False, url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribing = User.objects.filter(subscribers__user=request.user)
        limit = request.query_params.get('limit')
        if limit:
            subscribing = subscribing[:int(limit)]
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(subscribing, request)
        serializer = SubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        ['post', 'delete'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        self.get_object()
        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'subscribing': id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            Subscribe.objects.get(
                user=request.user, subscribing__id=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscribe.DoesNotExist:
            return Response(
                {'subscribed': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
