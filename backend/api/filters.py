import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, Tag


User = get_user_model()


class NameFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = 'name',


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.Filter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.Filter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = 'author',

    def filter_is_favorited(self, recipes, name, value):
        if self.request.user.is_authenticated and value == '1':
            return recipes.filter(favorite_recipe__user=self.request.user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        if self.request.user.is_authenticated and value == '1':
            return recipes.filter(shoppingcart_recipe__user=self.request.user)
        return recipes
