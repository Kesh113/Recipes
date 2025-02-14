import math

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

    def lookups(self, request, model_admin):
        recipes = model_admin.model.objects.all()
        cooking_times = sorted(recipe.cooking_time for recipe in recipes)
        count = len(cooking_times)
        if count < 3:
            threshold_25 = cooking_times[0]
            threshold_75 = cooking_times[-1]
        else:
            threshold_25 = cooking_times[math.ceil(count * 0.25) - 1]
            threshold_75 = cooking_times[math.ceil(count * 0.75) - 1]
        self.cooking_time_filters = {
            'fast': {'cooking_time__lte': threshold_25},
            'middle': {
                'cooking_time__gt': threshold_25,
                'cooking_time__lt': threshold_75
            },
            'slow': {'cooking_time__gte': threshold_75}
        }
        fast = recipes.filter(**self.cooking_time_filters['fast']).count()
        middle = recipes.filter(**self.cooking_time_filters['middle']).count()
        slow = recipes.filter(**self.cooking_time_filters['slow']).count()
        return (
            ('fast', f'До {threshold_25 + 1} мин ({fast})'),
            ('middle', f'До {threshold_75} мин ({middle})'),
            ('slow', f'{threshold_75} минут и более ({slow})')
        )

    def queryset(self, request, recipes):
        if self.value() == 'fast':
            return recipes.filter(**self.cooking_time_filters['fast'])
        elif self.value() == 'middle':
            return recipes.filter(**self.cooking_time_filters['middle'])
        elif self.value() == 'slow':
            return recipes.filter(**self.cooking_time_filters['slow'])


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

    @admin.display(description='Фото')
    @mark_safe
    def image_thumbnail(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="40" height="40" />'
        return 'Нет фото'

    @admin.display(description='Тэги')
    @mark_safe
    def tags_list(self, recipe):
        tags = ''.join([f'<li>{tag.name}</li>' for tag in recipe.tags.all()])
        return f'<ul>{tags}</ul>'

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list(self, recipe):
        ingredients = ''.join([
            f'<li>{ingredient.name}</li>'
            for ingredient in recipe.ingredients.all()
        ])
        return f'<ul>{ingredients}</ul>'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_list')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Рецепты')
    @mark_safe
    def recipe_list(self, ingredient):
        return ingredient.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_list')
    search_fields = ('name', 'slug')
    list_filter = ('name',)

    @admin.display(description='Рецепты')
    @mark_safe
    def recipe_list(self, tag):
        return tag.recipes.count()


@admin.register(Favorite, ShoppingCart)
class RecipeListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)


class RelatedObjectsFilter(admin.SimpleListFilter):
    related_name = None
    title = None

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()
        return users.filter(**{f'{self.related_name}__isnull': True})


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
class FoodgramUserAdmin(UserAdmin):
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
        return f"{user.first_name} {user.last_name}"

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_thumbnail(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="40" height="40" />'
        return 'Нет аватара'

    @admin.display(description='Кол-во рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Кол-во подписок')
    def subscriber_count(self, user):
        return user.subscribers.count()

    @admin.display(description='Кол-во подписчиков')
    def author_count(self, user):
        return user.authors.count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')
