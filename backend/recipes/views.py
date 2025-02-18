from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


RECIPE_NOT_FOUND = 'Рецепт с id = {} не найден.'


def recipe_redirect(request, pk):
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f'/recipes/{pk}')
    return Http404(RECIPE_NOT_FOUND.format(pk))
