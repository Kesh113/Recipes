from .import_json import ImportJsonCommand
from recipes.models import Tag


class Command(ImportJsonCommand):
    help = 'Импорт тегов из JSON файла.'
    model = Tag
    single_object_name = 'тэг'
