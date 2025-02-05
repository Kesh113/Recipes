from collections import defaultdict
import io


def get_shopping_data(recipes):
    ingredients = defaultdict(lambda: {'amount': 0, 'unit': ''})
    for recipe in recipes:
        for item in recipe.recipe_ingredients.all():
            name = item.ingredient.name
            amount = item.amount
            unit = item.ingredient.measurement_unit
            if name in ingredients:
                ingredients[name]['amount'] += amount
            else:
                ingredients[name]['amount'] = amount
                ingredients[name]['unit'] = unit
    return ingredients


def generate_shopping_list(recipes):
    output = io.BytesIO()
    output.write(b'Shopping list\n\n')
    for name, data in get_shopping_data(recipes).items():
        output.write(f'{name} - {data["amount"]} {data["unit"]}\n'.encode('utf-8'))
    output.seek(0)
    return output


def pop_fields(queryset, fields):
    [obj.pop(field) for obj in queryset for field in fields]