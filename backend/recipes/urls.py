from django.contrib import admin
from django.urls import path

from .views import recipe_redirect


admin.site.site_header = 'Администрирование приложения «Recipes»'


urlpatterns = [
    path('s/<int:pk>/', recipe_redirect, name='short-link')
]
