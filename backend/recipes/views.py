from django.urls import reverse
from django.views.generic import RedirectView


class RecipeRedirectView(RedirectView):
    permanent = True
    pattern_name = 'recipes-detail'

    # def get_redirect_url(self, request, pk):
    #     return f'{request.scheme}://{request.get_host()}/recipes/{pk}'
