from django.contrib.auth import models as auth_models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models


SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'

MIN_VALUE = 1


class FoodgramUser(auth_models.AbstractUser):
    email = models.EmailField(
        'Email', max_length=254, unique=True, blank=False, null=False
    )
    avatar = models.ImageField(
        upload_to='recipes/avatars/', verbose_name='Аватар',
        null=True, default=''
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


class Ingredient(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(max_length=64,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name[:21]} в {self.measurement_unit[:21]}'


class Tag(models.Model):
    name = models.CharField(max_length=32, unique=True,
                            verbose_name='Название')
    slug = models.SlugField(
        max_length=32, unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:21]


class Recipe(models.Model):
    author = models.ForeignKey(FoodgramUser, on_delete=models.CASCADE,
                               verbose_name='Автор')
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/recipes', verbose_name='Фото')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE)],
        verbose_name='Время приготовления (в минутах)',
    )
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список продуктов',
        through='RecipeIngredients',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Список тэгов')

    @property
    def favorites_count(self):
        return self.favorite_recipe.count()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author} - {self.name[:21]}'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Продукт'
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_VALUE)],
        verbose_name='Мера'
    )

    def __str__(self):
        return (f'{self.ingredient.name[:21]} - {self.amount} '
                f'{self.ingredient.measurement_unit[:21]}')

    class Meta:
        verbose_name = 'Количество продукта'
        verbose_name_plural = 'Количество продуктов'
        default_related_name = 'recipe_ingredients'


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s_user'.lower()
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s_recipe'.lower()
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_user_recipe'.lower()
            )
        ]
        abstract = True


class Favorite(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'У {self.user.username[:21]} в избранном {self.recipe}'


class ShoppingCart(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Списки покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return f'У {self.user.username[:21]} в списке покупок {self.recipe}'
