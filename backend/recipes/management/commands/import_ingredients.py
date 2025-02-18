from .import_json import ImportJsonCommand
from recipes.models import Ingredient


class Command(ImportJsonCommand):
    model = Ingredient
