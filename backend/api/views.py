from functools import wraps

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .filters import LimitFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    SubscribeSerializer, IngredientSerializer, TagSerializer, TokenSerializer,
    ReadRecipeSerializer, UserAvatarSerializer, WriteRecipeSerializer,
    UserRecipeListsSerializer
)
from .utils import generate_shopping_list
from foodgram.models import Favorite, Ingredient, ShoppingCart, Tag, Recipe
from users.models import Subscribe


User = get_user_model()

NOT_RECIPE_IN_FAVORITE = {'favorite': 'Рецепта нет в избранном'}

NOT_RECIPE_IN_SHOPPING_CART = {'shopping_cart': 'Рецепта нет в списке покупок'}

FILENAME = 'shopping_list.txt'

NOT_SUBSCRIBED = {'subscribed': 'Вы не подписаны на этого пользователя'}


def recipe_list_action(model, not_found_message):
    def decorator(func):
        @action(
            ['post', 'delete'], detail=True, url_path=func.__name__,
            permission_classes=[IsAuthenticated]
        )
        @wraps(func)
        def wrapper(self, request, pk):
            recipe = self.get_object()
            if request.method == 'POST':
                serializer = UserRecipeListsSerializer(
                    data={'recipe': recipe.id}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user, model=model)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            try:
                instance = model.objects.get(user=request.user, recipe=recipe)
                instance.delete()
                Response(status=status.HTTP_204_NO_CONTENT)
            except model.DoesNotExist:
                return Response(
                    not_found_message, status=status.HTTP_400_BAD_REQUEST
                )
        return wrapper
    return decorator


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

    @recipe_list_action(Favorite, NOT_RECIPE_IN_FAVORITE)
    def favorite(self, request, pk):
        pass

    @recipe_list_action(ShoppingCart, NOT_RECIPE_IN_SHOPPING_CART)
    def shopping_cart(self, request, pk):
        pass

    @action(
        ['get'], detail=True, url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe_url = request.build_absolute_uri(
            reverse('recipes-detail', args=[pk])
        )
        serializer = TokenSerializer(data={'full_url': recipe_url})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ['get'], detail=False, url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(shopping_carts__user=request.user)
        return FileResponse(
            generate_shopping_list(recipes),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=FILENAME
        )


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
        subscribing = self.filter_queryset(
            User.objects.filter(subscribers__user=request.user)
        )
        paginator = PageNumberPagination()
        serializer = SubscribeSerializer(
            paginator.paginate_queryset(subscribing, request),
            many=True, context={'request': request}
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
            return Response(NOT_SUBSCRIBED, status=status.HTTP_400_BAD_REQUEST)
