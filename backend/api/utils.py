from datetime import date


HEADER_ROW = 'Список продуктов пользователя {} на {}'

INGREDIENT_ROW = '{}. {} - {} {}'

RECIPES_ROW = '- {}'


def generate_shopping_list(user, recipes, ingredients_data):
    ingredient_rows = [
        INGREDIENT_ROW.format(
            i,
            ingredient[0].name.capitalize(),
            ingredient[1],
            ingredient[0].measurement_unit
        ) for i, ingredient in enumerate(ingredients_data.items(), 1)
    ]
    text = '\n'.join([
        HEADER_ROW.format(user, date.today()),
        'Продукты:',
        *ingredient_rows,
        'Рецепты:',
        *[RECIPES_ROW.format(recipe.name) for recipe in recipes],
    ])
    return text
