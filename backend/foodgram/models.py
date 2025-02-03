from decimal import Decimal
import random
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(max_length=64,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'

    def __str__(self):
        return f'{self.name[:21]} в {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True,
                            verbose_name='Название')
    slug = models.SlugField(max_length=32, null=True, blank=True, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name[:21]}'


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор')
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='foodgram/', verbose_name='Фото')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления',
        help_text='в минутах'
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
        through='RecipeIngredients'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Список тэгов')
    favorites_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество добавлений в избранное'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author} - {self.name[:21]}'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецепт', related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name='Количество'
    )

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь',
                             related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
                               related_name='users_favorite')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'У {self.user.username} в избранном {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь',
                             related_name='shopping_cart_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
                               related_name='users_shopping_cart')

    class Meta:
        verbose_name = 'Списки покупок'
        verbose_name_plural = 'Список покупок'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'У {self.user.username} в списке покупок {self.recipe}'


class Tokens(models.Model):
    full_url = models.URLField(unique=True, verbose_name='Ссылка')
    short_link = models.URLField(
        unique=True,
        db_index=True,
        blank=True,
        verbose_name='Короткая ссылка'
    )
    requests_count = models.IntegerField(default=0, verbose_name='Количество запросов')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ('-created_date',)

    def save(self, *args, **kwargs):
        if not self.short_link:
            while True:
                self.short_link = settings.SITE_URL + ''.join(
                    random.choices(
                        settings.CHARACTERS,
                        k=settings.TOKEN_LENGTH
                    )
                )
                if not Tokens.objects.filter(
                    short_link=self.short_link
                ).exists():
                    break
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.short_link} -> {self.full_url}'
    

