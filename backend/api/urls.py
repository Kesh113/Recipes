from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, TagViewSet, RecipeViewSet, FoodgramUserViewSet


router_v1 = DefaultRouter()
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', FoodgramUserViewSet, basename='user')


urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
