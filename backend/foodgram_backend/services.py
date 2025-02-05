from django.http import HttpResponse
from django.shortcuts import redirect

from foodgram.models import Tokens


def get_full_url(url: str) -> str:
    """
    Достаем полную ссылку по short_link
    Если ссылки нет в базе или она не активна
    возвращаем ошибку.
    Если все ок, то добавляем к счетчику статистики 1
    и возвращаем полную ссылку.
    """
    try:
        token = Tokens.objects.get(short_link=url)
        if not token.is_active:
            raise KeyError('Токен больше не доступен')
    except Tokens.DoesNotExist:
        raise KeyError('Попробуйте другой url. Таких url в базе данных нет')
    token.requests_count += 1
    token.save()
    return token.full_url


def redirection(request):
    """Перенаправляем пользователя по ссылке"""
    try:
        return redirect(get_full_url(request.build_absolute_uri()[:-1]))
    except Exception as e:
        return HttpResponse(e.args)
