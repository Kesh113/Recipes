from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from .utils import validate_username


USERNAME_HELP_TEXT = ('Обязательное поле. Только буквы,'
                      ' цифры и @/./+/-/_.')


class FoodgramUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text=USERNAME_HELP_TEXT,
        validators=(validate_username,),
        verbose_name='Логин'
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('Email', max_length=254, unique=True)
    avatar = models.ImageField(upload_to='users/', verbose_name='Аватар', null=True, default='')

    def __str__(self):
        return f'{self.username[:21]}'

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = 'username',


class Subscribe(models.Model):
    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscriptions'
    )
    subscribing = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Подписать на',
        related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'subscribing')

    def __str__(self):
        return f'{self.user.username} подписан на {self.subscribing.username}'

    def clean_subscribing(self):
        if self.user == self.subscribing:
            raise ValidationError('Нельзя подписаться на самого себя.')
