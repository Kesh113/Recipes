import django_filters

from foodgram.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(field_name='tags__slug')
    is_favorited = django_filters.Filter(method='filter_is_favorited', label='is_favorited')
    is_in_shopping_cart = django_filters.Filter(method='filter_is_in_shopping_cart', label='is_in_shopping_cart')

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
