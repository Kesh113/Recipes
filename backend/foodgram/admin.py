from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Favorites, Follow, Ingredient, Recipe,
                     RecipeIngredients, ShoppingList, Tag)


class UsersAdmin(UserAdmin):
    search_fields = ('email', 'username')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
    list_display_links = ('title',)
    search_fields = ('author', 'title')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('tags',)
    readonly_fields = ('favorites_count',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('title', 'measure_unit')
    search_fields = ('title',)


admin.site.register([Tag, RecipeIngredients, Favorites, Follow, ShoppingList])
