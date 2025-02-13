from django.urls import path

from .views import RecipeRedirectView


urlpatterns = [
    path('s/<int:pk>/', RecipeRedirectView.as_view(), name='short-link')
]
