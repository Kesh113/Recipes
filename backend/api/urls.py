from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import FavoriteViewSet, IngredientViewSet, TagViewSet, RecipeViewSet, UserViewSet


router_v1 = DefaultRouter()
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register(r'recipes/(?P<post_id>[\d]+)/favorite', FavoriteViewSet, basename='favorite')
router_v1.register('users', UserViewSet, basename='user')

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
