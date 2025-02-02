from collections import defaultdict
import io
from django.http import FileResponse, StreamingHttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action, permission_classes
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
    FavoriteSerializer, ShoppingCartSerializer, SubscribeSerializer, IngredientSerializer,
    TagSerializer, ReadRecipeSerializer, UserAvatarSerializer, UserSerializer,
    CreateSubscribeSerializer, WriteRecipeSerializer, TokenSerializer
)
from foodgram.models import Favorite, Ingredient, ShoppingCart, Tag, Recipe, Tokens
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
    def get(self, request, recipe_id):
        get_object_or_404(Recipe, pk=recipe_id)
        recipe_url = request.build_absolute_uri(reverse('recipes-detail', args=[recipe_id]))
        serializer = TokenSerializer(data={'full_url': recipe_url})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FavoriteView(APIView):
    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        favorite_recipe, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response({'favorite': 'Рецепт уже добавлен в избранное'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteSerializer(favorite_recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({'favorite': 'Рецепта нет в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(APIView):
    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        favorite_recipe, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response({'favorite': 'Рецепт уже добавлен в избранное'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ShoppingCartSerializer(favorite_recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if not ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({'favorite': 'Рецепта нет в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes([IsAuthenticated])
class DownloadShoppingCartView(APIView):
    def get(self, request):
        user = request.user
        recipes = Recipe.objects.filter(users_shopping_cart__user=user)
        serializer = ReadRecipeSerializer(recipes, many=True)
        ingredients = defaultdict(lambda: {'amount': 0, 'unit': ''})
        for recipe in serializer.data:
            for ingredient in recipe['ingredients']:
                name = ingredient['name']
                amount = ingredient['amount']
                unit = ingredient['measurement_unit']
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name]['amount'] = amount
                    ingredients[name]['unit'] = unit

        def generate_shopping_list():
            output = io.StringIO()
            for name, data in ingredients.items():
                output.write(f'{name} - {data["amount"]} {data["unit"]}\n')
            yield output.getvalue()

        response = StreamingHttpResponse(generate_shopping_list(), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
