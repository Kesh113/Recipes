from datetime import date


HEADER_ROW = 'Список продуктов пользователя {} на {}'

INGREDIENT_ROW = '{}. {} - {} {}'

RECIPES_ROW = '- {}'


def generate_shopping_list(user, recipes, ingredients):
    ingredient_rows = [
        INGREDIENT_ROW.format(
            i,
            ingredient.name.capitalize(),
            ingredient.total_amount,
            ingredient.measurement_unit
        ) for i, ingredient in enumerate(ingredients, 1)
    ]
    return '\n'.join([
        HEADER_ROW.format(user, date.today()),
        'Продукты:',
        *ingredient_rows,
        'Рецепты:',
        *[RECIPES_ROW.format(recipe) for recipe in recipes],
    ])
