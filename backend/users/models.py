from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.db import models


SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'


class FoodgramUser(auth_models.AbstractUser):
    email = models.EmailField(
        'Email', max_length=254, unique=True, blank=False, null=False
    )
    avatar = models.ImageField(
        upload_to='users/', verbose_name='Аватар', null=True, default=''
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username[:21]

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = 'username', 'email'


class Subscribe(models.Model):
    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribers'
    )
    subscribing = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='authors'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'subscribing'], name='unique_subscription'
        )]

    def __str__(self):
        return (f'{self.user.username[:21]} подписан на '
                f'{self.subscribing.username[:21]}')

    def clean(self):
        if self.user == self.subscribing:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)
