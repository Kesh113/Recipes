from functools import wraps

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
    IngredientSerializer, TagSerializer,
    ReadRecipeSerializer, UserAvatarSerializer, WriteRecipeSerializer
)
from .utils import generate_shopping_list
from recipes.models import (
    Favorite, Ingredient, ShoppingCart, Tag, Recipe, Subscribe
)


User = get_user_model()

ALREADY_IN_FAVORITE = {'favorite': 'Рецепт уже добавлен в избранное'}

ALREADY_IN_SHOPPING_CART = {
    'shopping_cart': 'Рецепт уже добавлен в список покупок'
}

EXCLUDE_RECIPE_FIELDS = [
    'tags', 'author', 'ingredients',
    'text', 'is_favorited', 'is_in_shopping_cart'
]

NOT_RECIPE_IN_FAVORITE = {'favorite': 'Рецепта нет в избранном'}

NOT_RECIPE_IN_SHOPPING_CART = {'shopping_cart': 'Рецепта нет в списке покупок'}

FILENAME = 'shopping_list.txt'

SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = {'subscribe': 'Вы уже подписаны'}

NOT_SUBSCRIBED = {'subscribe': 'Вы не подписаны на этого пользователя'}


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

    def _recipe_list_action(
            model, not_found_message, url_path, already_in_list
    ):
        def decorator(func):
            @action(
                ['post', 'delete'], detail=True, url_path=url_path,
                permission_classes=[IsAuthenticated]
            )
            @wraps(func)
            def wrapper(self, request, pk):
                recipe = self.get_object()
                if request.method == 'POST':
                    favorite_recipe, created = model.objects.get_or_create(
                        user=request.user, recipe=recipe
                    )
                    if not created:
                        raise serializers.ValidationError(already_in_list)
                    recipe_data = ReadRecipeSerializer(
                        favorite_recipe.recipe, context={'request': request}
                    ).data
                    [recipe_data.pop(field) for field in EXCLUDE_RECIPE_FIELDS]
                    return Response(
                        recipe_data, status=status.HTTP_201_CREATED
                    )
                try:
                    instance = model.objects.get(
                        user=request.user, recipe=recipe
                    )
                    instance.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                except model.DoesNotExist:
                    raise serializers.ValidationError(not_found_message)
            return wrapper
        return decorator

    @_recipe_list_action(
        Favorite, NOT_RECIPE_IN_FAVORITE,
        'favorite', ALREADY_IN_FAVORITE
    )
    def favorite(self, request, pk):
        pass

    @_recipe_list_action(
        ShoppingCart, NOT_RECIPE_IN_SHOPPING_CART,
        'shopping_cart', ALREADY_IN_SHOPPING_CART
    )
    def shopping_cart(self, request, pk):
        pass

    @action(
        ['get'], detail=True, url_path='get-link',
    )
    def get_link(self, request, pk):
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
        recipes = Recipe.objects.filter(shoppingcart_recipe__user=request.user)
        return FileResponse(
            generate_shopping_list(recipes),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=FILENAME
        )


class FoodgramUserViewSet(UserViewSet):
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

    def _get_serialized_recipes(self, subscribing):
        subscribing_recipes = subscribing.recipes.all()
        recipes_limit = self.request.GET.get('recipes_limit')
        if recipes_limit and isinstance(recipes_limit, str):
            subscribing_recipes = subscribing_recipes[
                :int(recipes_limit)
            ]
        serialized_recipes = ReadRecipeSerializer(
            subscribing_recipes, many=True
        ).data
        [obj.pop(field) for obj in serialized_recipes
            for field in EXCLUDE_RECIPE_FIELDS]
        return serialized_recipes

    @action(
        ['get'], detail=False, url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribes = []
        for subscribing in self.get_queryset().filter(
            authors__user=request.user
        ):
            recipes_data = self._get_serialized_recipes(subscribing)
            subscribing_data = self.get_serializer_class()(
                subscribing, context={'request': request}
            ).data
            subscribing_data['recipes'] = recipes_data
            subscribing_data['recipes_count'] = len(recipes_data)
            subscribes.append(subscribing_data)
        return self.get_paginated_response(self.paginate_queryset(subscribes))

    @action(
        ['post', 'delete'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        subscribing = self.get_object()
        if request.method == 'POST':
            if request.user == subscribing:
                raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)
            subscribe, created = Subscribe.objects.get_or_create(
                user=request.user, subscribing=subscribing
            )
            if not created:
                raise serializers.ValidationError(ALREADY_SUBSCRIBED_ERROR)
            subscribing_data = self.get_serializer_class()(
                subscribing, context={'request': request}
            ).data
            serialized_recipes = self._get_serialized_recipes(subscribing)
            subscribing_data.update({
                'recipes': serialized_recipes,
                'recipes_count': len(serialized_recipes)
            })
            return Response(subscribing_data, status=status.HTTP_201_CREATED)
        get_object_or_404(
            Subscribe, user=request.user, subscribing=subscribing
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
