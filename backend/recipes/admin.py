from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, Subscribe,
    RecipeIngredients, ShoppingCart, Tag
)


User = get_user_model()


class RecipeIngredientsAdmin(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def _get_filter_recipes(self, range_name):
        return Recipe.objects.filter(
            cooking_time__range=self.cooking_time_filters[range_name]
        )

    def lookups(self, request, model_admin):
        cooking_times = sorted(set(
            recipe.cooking_time for recipe in model_admin.model.objects.all()
        ))
        count = len(cooking_times)
        if count < 3:
            return
        threshold_25 = cooking_times[count // 4]
        threshold_75 = cooking_times[(count * 3) // 4]
        self.cooking_time_filters = {
            'fast': (cooking_times[0], threshold_25),
            'middle': (threshold_25, threshold_75),
            'slow': (threshold_75, cooking_times[-1])
        }
        fast = self._get_filter_recipes('fast').count()
        middle = self._get_filter_recipes('middle').count()
        slow = self._get_filter_recipes('slow').count()
        return (
            ('fast', f'До {threshold_25} мин ({fast})'),
            ('middle', f'До {threshold_75} мин ({middle})'),
            ('slow', f'{threshold_75} минут и более ({slow})')
        )

    def queryset(self, request, recipes):
        return (
            self._get_filter_recipes(self.value()) if self.value()
            else recipes
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author', 'tags_list',
        'favorites_count', 'ingredients_list', 'image_thumbnail'
    )
    list_display_links = ('name',)
    search_fields = ('author__username', 'name', 'tags__name')
    list_filter = ('tags', 'author', CookingTimeFilter)
    readonly_fields = 'favorites_count',
    inlines = [RecipeIngredientsAdmin]

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Фото')
    @mark_safe
    def image_thumbnail(self, recipe):
        return f'<img src="{recipe.image.url}" width="40" height="40" />'

    @admin.display(description='Тэги')
    @mark_safe
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list(self, recipe):
        return '<br>'.join(
            f'{recipe_ingredient.ingredient.name} - {recipe_ingredient.amount}'
            f' {recipe_ingredient.ingredient.measurement_unit}'
            for recipe_ingredient in recipe.recipe_ingredients.all()
        )


class RecipeCountMixin:
    @admin.display(description='Рецептов')
    def recipe_count(self, model):
        return model.recipes.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin, RecipeCountMixin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, RecipeCountMixin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Favorite, ShoppingCart)
class RecipeListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)


class RelatedObjectsFilter(admin.SimpleListFilter):
    related_name = None
    title = None
    CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.related_filters = {
            'yes': {f'{self.related_name}__isnull': False},
            'no': {f'{self.related_name}__isnull': True},
        }

    def lookups(self, request, model_admin):
        return self.CHOICES

    def queryset(self, request, users):
        if self.value():
            return users.filter(
                **self.related_filters[self.value()]
            ).distinct()
        return users


class HasRecipesFilter(RelatedObjectsFilter):
    title = 'Имеет рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(RelatedObjectsFilter):
    title = 'Имеет подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscribers'


class HasFollowersFilter(RelatedObjectsFilter):
    title = 'Имеет подписчиков'
    parameter_name = 'has_subscribers'
    related_name = 'authors'


@admin.register(User)
class FoodgramUserAdmin(UserAdmin, RecipeCountMixin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('avatar',)}),)
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_thumbnail',
        'recipe_count', 'subscriber_count', 'author_count'
    )
    list_display_links = ('username',)
    search_fields = ('email', 'username')
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_thumbnail(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="40" height="40" />'
        return ''

    @admin.display(description='Подписок')
    def subscriber_count(self, user):
        return user.subscribers.count()

    @admin.display(description='Подписчиков')
    def author_count(self, user):
        return user.authors.count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')
