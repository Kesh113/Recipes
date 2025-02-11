import csv
import os
from django.core.management.base import BaseCommand
from foodgram.models import Ingredient


MODELS = {
    'ingredients.csv': Ingredient,
}

DATA_DIR = 'data/'


class Command(BaseCommand):
    help = 'Загрузка данных из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Загружает все CSV-файлы из папки data/'
        )

    def handle(self, *args, **options):
        if options['all']:
            for file_name, model in MODELS.items():
                try:
                    with open(
                        os.path.join(DATA_DIR, file_name),
                        encoding='utf-8'
                    ) as file:
                        reader = csv.reader(file)
                        for row in reader:
                            name, measurement_unit = row
                            instance, created = (
                                model.objects.update_or_create(
                                    name=name,
                                    defaults={
                                        'measurement_unit': measurement_unit
                                    }
                                )
                            )
                            if created:
                                self.stdout.write(self.style.SUCCESS(
                                    f"Создан объект {instance}"))
                            else:
                                self.stdout.write(self.style.SUCCESS(
                                    f"Обновлен объект {instance}"))
                except FileNotFoundError:
                    self.stderr.write(self.style.ERROR(
                        f"Файл {file_name} не найден"
                    ))
        else:
            print(
                'Используйте "--all" для загрузки всех '
                'CSV-файлов из папки data/'
            )
