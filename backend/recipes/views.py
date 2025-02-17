from django.shortcuts import redirect

from recipes.models import Recipe


def recipe_redirect(request, pk):
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(
            request.build_absolute_uri(f'/recipes/{pk}'),
        )
    return redirect('/not-found')
