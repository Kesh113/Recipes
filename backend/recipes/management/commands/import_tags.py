from .import_json import ImportJsonCommand
from recipes.models import Tag


class Command(ImportJsonCommand):
    model = Tag
