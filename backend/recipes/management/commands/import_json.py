import json

from django.core.management import base


class ImportJsonCommand(base.BaseCommand):
    help = None
    model = None
    single_object_name = None

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file_path', help='Путь к JSON файлу.'
        )

    def _declension_word(self, count):
        if count % 10 == 1 and count % 100 != 11:
            return self.single_object_name
        elif count % 10 in range(2, 5) and count % 100 not in range(12, 15):
            return f'{self.single_object_name}а'
        return f'{self.single_object_name}ов'

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
                f'{total_objects} {self._declension_word(total_objects)} '
                f'успешно импортировано из {file_path}'
            ))
        except Exception as e:
            raise base.CommandError(
                f'Ошибка при импорте ингредиентов {file_path}: {e}'
            )
