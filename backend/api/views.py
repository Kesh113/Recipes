from datetime import date
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.formats import date_format
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from .filters import LimitFilter, NameFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeListSerializer, SubscribedUserSerializer,
    TagSerializer, ReadRecipeSerializer, UserAvatarSerializer,
    WriteRecipeSerializer
)
from .utils import generate_shopping_list
from recipes.models import (
    Favorite, Ingredient, ShoppingCart, Tag, Recipe, Subscribe
)


User = get_user_model()

RECIPE_NOT_EXIST = 'Рецепта с id={} не существует'

ALREADY_IN_RECIPE_LIST = 'Рецепт "{}" уже добавлен'

FILENAME = 'shopping_list({}).txt'

SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на "{}"'

DATE_FORMAT_SHORT = 'd.m.Y'


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
        if request.method == 'DELETE':
            get_object_or_404(model, user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
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
        if not self.get_queryset().filter(pk=pk).exists():
            raise serializers.ValidationError(RECIPE_NOT_EXIST.format(pk))
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
        ingredients = (
            Ingredient.objects.filter(recipes__in=recipes)
            .annotate(total_amount=Sum('recipe_ingredients__amount'))
            .order_by('name')
        )
        return FileResponse(
            generate_shopping_list(request.user, recipes, ingredients),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=FILENAME.format(
                date_format(date.today(), DATE_FORMAT_SHORT)
            )
        )


class FoodgramUserViewSet(UserViewSet):
    filter_backends = DjangoFilterBackend,
    filterset_class = LimitFilter

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        ['put', 'delete'], detail=False, url_path='me/avatar'
    )
    def me_avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ['get'], detail=False, url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribe_data = SubscribedUserSerializer(
            self.filter_queryset(self.get_queryset().filter(
                authors__user=request.user
            )), context={'request': request}, many=True
        ).data
        return self.get_paginated_response(
            self.paginate_queryset(subscribe_data)
        )

    @action(
        ['post', 'delete'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        author = self.get_object()
        if request.method == 'DELETE':
            get_object_or_404(
                Subscribe, user=request.user, subscribing=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.user == author:
            raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)
        _, created = Subscribe.objects.get_or_create(
            user=request.user, subscribing=author
        )
        if not created:
            raise serializers.ValidationError(
                {'subscribe': ALREADY_SUBSCRIBED_ERROR.format(author)}
            )
        return Response(SubscribedUserSerializer(
            author, context={'request': request}
        ).data, status=status.HTTP_201_CREATED)
