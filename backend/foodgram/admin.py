from django.contrib import admin


from .models import (Favorites, Ingredient, Recipe,
                     RecipeIngredients, ShoppingCart, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_display_links = ('name',)
    search_fields = ('author', 'name')
    list_filter = ('tags',)
    readonly_fields = 'favorites_count',


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register([Tag, RecipeIngredients, Favorites, ShoppingCart])
