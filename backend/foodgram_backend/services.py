from django.views.generic import RedirectView

from .utils import generate_url
from foodgram.models import Tokens


TOKEN_NOT_AVAILABLE = 'Токен больше не доступен'

TOKEN_NOT_EXIST = 'Попробуйте другой URL. Такого URL в базе данных нет'


class TokenRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        try:
            token = Tokens.objects.get(
                short_link=self.request.path.strip('/')
            )
            if not token.is_active:
                raise ValueError(TOKEN_NOT_AVAILABLE)
        except Tokens.DoesNotExist:
            raise ValueError(TOKEN_NOT_EXIST)
        token.requests_count += 1
        token.save()
        return generate_url(
            self.request, url_path=f'recipes/{token.recipe.id}'
        )
