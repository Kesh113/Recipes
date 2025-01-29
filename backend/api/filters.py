import django_filters

from foodgram.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'users_favorite__is_favorited', 'tags', 'users_shopping_list__is_in_shopping_cart')
