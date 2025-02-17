from .import_json import ImportJsonCommand
from recipes.models import Ingredient


class Command(ImportJsonCommand):
    help = 'Импорт ингредиентов из JSON файла.'
    model = Ingredient
    single_object_name = 'ингредиент'
