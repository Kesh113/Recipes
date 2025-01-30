from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


FORBIDDEN_USE = 'Использовать имя "{}" в качестве username запрещено.'

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message=(
        'Введите действительное имя пользователя. '
        'Это значение может содержать только буквы '
        'числа, и символы: @/./+/-/_ .'
    )
)


def validate_username(username: str):
    username_validator(username)
    if username == settings.USERNAME_RESERVED:
        raise ValidationError(
            {'username': FORBIDDEN_USE.format(settings.USERNAME_RESERVED)}
        )
    return username
