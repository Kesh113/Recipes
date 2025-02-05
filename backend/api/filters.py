import django_filters
from django.contrib.auth import get_user_model

from foodgram.models import Recipe, Tag


User = get_user_model()


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.Filter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.Filter(method='filter_is_in_shopping_cart')
    limit = django_filters.NumberFilter(method='filter_limit')

    class Meta:
        model = Recipe
        fields = 'author',

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value == '1':
            return queryset.filter(users_favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value == '1':
            return queryset.filter(users_shopping_cart__user=self.request.user)
        return queryset

    def filter_limit(self, queryset, name, value):
        return queryset[:value] if value else queryset


class LimitFilter(django_filters.FilterSet):
    limit = django_filters.NumberFilter(method='filter_limit')

    class Meta:
        model = User
        fields = ()

    def filter_limit(self, queryset, name, value):
        return queryset[:value] if value else queryset
