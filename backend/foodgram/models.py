from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models


User = get_user_model()


class Ingredient(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    measure_unit = models.CharField(max_length=21,
                                    verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'

    def __str__(self):
        return f'{self.title[:21]} в {self.measure_unit}'


class Tag(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        default_related_name = 'tags'

    def __str__(self):
        return f'{self.title[:21]}'


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор')
    title = models.CharField(max_length=100, verbose_name='Название')
    image = models.ImageField(upload_to='foodgram/', verbose_name='Фото')
    description = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        help_text='в минутах'
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredients')
    tags = models.ManyToManyField(Tag)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author} - {self.title[:21]}'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return (f'{self.ingredient.title} - {self.quantity} '
                f'{self.ingredient.measure_unit}')

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'


class Favorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='users_favorite')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'У {self.user.username} в избранном {self.recipe}'


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='followers')
    following = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='followings')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'following')

    def __str__(self):
        return f'{self.user.username} подписан на {self.following.username}'

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя.')


class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_list_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='users_shopping_list')

    class Meta:
        verbose_name = 'Покупки'
        verbose_name_plural = 'Покупка'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'У {self.user.username} в списке покупок {self.recipe}'
