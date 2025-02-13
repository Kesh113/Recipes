import csv
import os

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from foodgram.models import Ingredient, Tag


MODELS = {
    'ingredients.csv': Ingredient,
    'tags.csv': Tag
}

DATA_DIR = 'foodgram/fixtures/'


class Command(BaseCommand):
    help = 'Загрузка данных из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_name',
            help='Укажите название CSV файла без расширения'
        )

    def handle(self, *args, **options):
        file_name = options['file_name']
        if file_name:
            file_name = f'{file_name}.csv'
            Model = MODELS[file_name]
            try:
                with open(
                    os.path.join(DATA_DIR, file_name),
                    encoding='utf-8'
                ) as file:
                    reader = csv.DictReader(file)
                    objects = []
                    for row in reader:
                        if Model.__name__ == 'Ingredient':
                            name, measurement_unit = (
                                row['name'], row['measurement_unit']
                            )
                            objects.append(Model(
                                name=name, measurement_unit=measurement_unit
                            ))
                        elif Model.__name__ == 'Tag':
                            name, slug = row['name'], row['slug']
                            objects.append(Model(name=name, slug=slug))
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    'Используйте "ingredients" или "tags" '
                                    'для загрузки CSV-файлов из папки '
                                    'foodgram/fixtures'
                                )
                            )
                    try:
                        Model.objects.bulk_create(objects)
                        self.stdout.write(self.style.SUCCESS(
                            'Данные успешно импортированы в модель '
                            f'{Model.__name__} из {file_name}'
                        ))
                    except IntegrityError as e:
                        self.stdout.write(
                            self.style.WARNING(
                                'Ошибка целостности при добавлении данных '
                                f'{file_name}: {e}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Ошибка при импорте данных из {file_name}: {e}'
                            )
                        )
            except FileNotFoundError:
                self.stderr.write(self.style.ERROR(
                    f'Файл {file_name} не найден'
                ))
