import json

from django.core.management import base


class ImportJsonCommand(base.BaseCommand):
    help = 'Импорт JSON файла.'
    model = None

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file_path', help='Путь к JSON файлу.'
        )

    def handle(self, *args, **options):
        try:
            file_path = options['json_file_path']
            with open(file_path, 'r', encoding='utf-8') as file:
                objects = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                )
            total_objects = len(objects)
            self.stdout.write(self.style.SUCCESS(
                f'{total_objects} '
                f'{self.model._meta.verbose_name_plural.lower()} '
                f'успешно импортировано из {file_path}'
            ))
        except Exception as e:
            raise base.CommandError(
                f'Ошибка при импорте ингредиентов {file_path}: {e}'
            )
