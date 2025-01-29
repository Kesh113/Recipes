from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class FoodgramUser(AbstractUser):
    avatar = models.ImageField(upload_to='users/', verbose_name='Аватар', blank=True, null=True)


class Follow(models.Model):
    user = models.ForeignKey(FoodgramUser, on_delete=models.CASCADE,
                             related_name='followers')
    following = models.ForeignKey(FoodgramUser, on_delete=models.CASCADE,
                                  related_name='followings')
    is_subscribed = models.BooleanField(default=False, db_index=True, verbose_name='Подписан')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'following')
        ordering = '-is_subscribed',

    def __str__(self):
        return f'{self.user.username} подписан на {self.following.username}'

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя.')
