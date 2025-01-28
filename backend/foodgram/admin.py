from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Favorites, Follow, Ingredient, Recipe,
                     RecipeIngredients, ShoppingList, Tag)


class UsersAdmin(UserAdmin):
    search_fields = ('email', 'username')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_display_links = ('name',)
    search_fields = ('author', 'name')
    list_filter = ('tags',)
    readonly_fields = ('get_favorites_count',)

    def get_favorites_count(self, obj):
        return Favorites.objects.filter(recipe=obj).count()

    get_favorites_count.short_description = 'Количество добавлений в избранное'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register([Tag, RecipeIngredients, Favorites, Follow, ShoppingList])
