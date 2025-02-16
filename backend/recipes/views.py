from django.shortcuts import redirect, get_object_or_404

from recipes.models import Recipe


def recipe_redirect(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(
        request.build_absolute_uri(f'/recipes/{pk}'),
        permanent=True
    )
