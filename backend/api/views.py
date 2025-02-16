from typing import OrderedDict

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .filters import NameFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeListSerializer, SubscribeSerializer,
    TagSerializer, ReadRecipeSerializer, UserAvatarSerializer,
    WriteRecipeSerializer
)
from .utils import generate_shopping_list
from recipes.models import (
    Favorite, Ingredient, RecipeIngredients, ShoppingCart,
    Tag, Recipe, Subscribe
)


User = get_user_model()

ALREADY_IN_RECIPE_LIST = 'Рецепт "{}" уже добавлен'

FILENAME = 'shopping_list.txt'

SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на "{}"'


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = DjangoFilterBackend,
    filterset_class = NameFilter
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

    def _handle_recipe_list_item(self, request, model):
        recipe = self.get_object()
        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                raise serializers.ValidationError(
                    {model.__name__: ALREADY_IN_RECIPE_LIST.format(recipe)}
                )
            return Response(
                RecipeListSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(model, user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ['post', 'delete'], detail=True, url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self._handle_recipe_list_item(request, Favorite)

    @action(
        ['post', 'delete'], detail=True, url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self._handle_recipe_list_item(request, ShoppingCart)

    @action(
        ['get'], detail=True, url_path='get-link',
    )
    def get_link(self, request, pk):
        get_object_or_404(self.get_queryset(), pk=pk)
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('short-link', args=(pk,))
            )
        })

    @action(
        ['get'], detail=False, url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(shoppingcarts__user=request.user)
        ingredients_data = OrderedDict()
        for recipe_ingredient in RecipeIngredients.objects.filter(
            recipe__in=recipes
        ):
            ingredients_data[recipe_ingredient.ingredient] = (
                ingredients_data.get(
                    recipe_ingredient.ingredient, 0
                ) + recipe_ingredient.amount
            )
        return FileResponse(
            generate_shopping_list(request.user, recipes, ingredients_data),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=FILENAME
        )


class FoodgramUserViewSet(UserViewSet):
    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

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
        subscribe_data = SubscribeSerializer(
            self.get_queryset().filter(
                authors__user=request.user
            ), context={'request': request}, many=True
        ).data
        return self.get_paginated_response(
            self.paginate_queryset(subscribe_data)
        )

    @action(
        ['post', 'delete'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        subscribing = self.get_object()
        if request.method == 'POST':
            if request.user == subscribing:
                raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)
            _, created = Subscribe.objects.get_or_create(
                user=request.user, subscribing=subscribing
            )
            if not created:
                raise serializers.ValidationError(
                    {'subscribe': ALREADY_SUBSCRIBED_ERROR.format(subscribing)}
                )
            subscribing_data = SubscribeSerializer(
                subscribing, context={'request': request}
            ).data
            return Response(subscribing_data, status=status.HTTP_201_CREATED)
        get_object_or_404(
            Subscribe, user=request.user, subscribing=subscribing
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
