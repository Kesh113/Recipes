from datetime import date

from django.utils.formats import date_format


HEADER_ROW = 'Список продуктов пользователя {} на {}'

INGREDIENT_ROW = '{}. {}: {} {}'

RECIPES_ROW = '{} (@{})'

DATE_FORMAT = 'd E Y'


def generate_shopping_list(user, recipes, ingredients):
    return '\n'.join([
        HEADER_ROW.format(
            user.username, date_format(date.today(), DATE_FORMAT)
        ),
        'Продукты:',
        *[
            INGREDIENT_ROW.format(
                i,
                ingredient.name.capitalize(),
                ingredient.total_amount,
                ingredient.measurement_unit
            ) for i, ingredient in enumerate(ingredients, 1)
        ],
        'Рецепты:',
        *[RECIPES_ROW.format(
            recipe.name[:21], recipe.author.username
        ) for recipe in recipes],
    ])
