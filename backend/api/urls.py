from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, TagViewSet, RecipeViewSet, UserViewSet, SubscribeViewSet, GetLinkView, FavoriteView, ShoppingCartView


router_v1 = DefaultRouter()
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('tags', TagViewSet, basename='tag')
# router_v1.register(r'recipes/(?P<recipe_id>\d+)/favorite', FavoriteViewSet, basename='favorite')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'users/(?P<user_id>[\d]+)/subscribe', SubscribeViewSet, basename='subscribe')
router_v1.register('users', UserViewSet, basename='user')


urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:recipe_id>/get-link/', GetLinkView.as_view(), name='get-link'),
    path('recipes/<int:recipe_id>/favorite/', FavoriteView.as_view(), name='favorite'),
    path('recipes/<int:recipe_id>/shopping_cart/', ShoppingCartView.as_view(), name='shopping_cart'),
    path('', include(router_v1.urls)),
]
