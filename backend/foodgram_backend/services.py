from django.views.generic import RedirectView

from foodgram.models import Tokens


class TokenRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        try:
            token = Tokens.objects.get(
                short_link=self.request.build_absolute_uri()[:-1]
            )
            if not token.is_active:
                raise ValueError('Токен больше не доступен')
        except Tokens.DoesNotExist:
            raise ValueError('Попробуйте другой URL. '
                             'Такого URL в базе данных нет')
        token.requests_count += 1
        token.save()
        return token.full_url
