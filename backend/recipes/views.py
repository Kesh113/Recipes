from django.views.generic import RedirectView


class RecipeRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        pk = kwargs['pk']
        return self.request.build_absolute_uri(f'/recipes/{pk}')
