from django.contrib import admin

from .models import Favorites, Follow, Ingredient, Recipe, RecipeIngredients, ShoppingList, Tag


admin.site.register([Recipe, Tag, Ingredient, RecipeIngredients, Favorites, Follow, ShoppingList])
