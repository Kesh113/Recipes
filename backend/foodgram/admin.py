from django.contrib import admin


from .models import (Favorite, Ingredient, Recipe,
                     RecipeIngredients, ShoppingCart, Tag, Tokens)


class RecipeIngredientsAdmin(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_display_links = ('name',)
    search_fields = ('author', 'name')
    list_filter = ('tags',)
    readonly_fields = 'favorites_count',
    inlines = [RecipeIngredientsAdmin]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tokens)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'short_link',
        'requests_count',
        'created_date',
        'is_active'
    )
    search_fields = ('recipe', 'short_link')


admin.site.register([Tag, Favorite, ShoppingCart])
