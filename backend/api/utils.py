from datetime import date

from django.db.models import Sum

from foodgram.models import RecipeIngredients


def get_ingredients(recipes):
    ingredients_data = (
        RecipeIngredients.objects
        .filter(recipe__in=recipes)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .values(
            'ingredient__name', 'ingredient__measurement_unit', 'total_amount'
        )
    )
    return [
        f'{i}. {data["ingredient__name"].capitalize()} - '
        f'{data["total_amount"]} {data["ingredient__measurement_unit"][:4]}'
        for i, data in enumerate(ingredients_data, 1)
    ]


def generate_shopping_list(recipes):
    text = '\n'.join([
        f'Список продуктов {date.today()}',
        'Продукты:',
        *get_ingredients(recipes),
        'Рецепты:',
        *[f'- {recipe.name}' for recipe in recipes],
    ])
    return text
