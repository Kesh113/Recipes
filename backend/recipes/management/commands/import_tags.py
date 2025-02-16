import json

from django.core.management import base

from recipes.models import Tag


class Command(base.BaseCommand):
    help = 'Импорт тегов из JSON файла.'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file_path', help='Путь к JSON файлу с тегами.'
        )

    def handle(self, *args, **options):
        try:
            file_path = options['json_file_path']
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                Tag.objects.bulk_create(Tag(**item) for item in data)
            self.stdout.write(self.style.SUCCESS(
                f'Теги успешно импортированы из {file_path}'
            ))
        except Exception as e:
            raise base.CommandError(f'Ошибка при импорте тегов: {e}')