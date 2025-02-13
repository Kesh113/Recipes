import json

from django.apps import apps
from django.core.management import base, call_command


class Command(base.BaseCommand):
    help = 'Загрузка данных из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file_path',
            help=(
                'Необходимо указать относительный путь до JSON файла.'
            )
        )
        parser.add_argument(
            'model',
            help=(
                'Полное имя модели (app_label.ModelName), '
                'в которую загружать данные.'
            )
        )

    def handle(self, *args, **options):
        json_file_path = options['json_file_path']
        model_name = options['model']
        try:
            app_label, model_name_short = model_name.split('.')
        except ValueError:
            raise base.CommandError(
                'Неправильный формат имени модели. '
                'Используйте app_label.ModelName'
            )
        try:
            Model = apps.get_model(app_label, model_name_short)
        except LookupError:
            raise base.CommandError(f'Модель "{model_name}" не найдена.')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            raise base.CommandError(f'Файл "{json_file_path}" не найден.')
        except json.JSONDecodeError:
            raise base.CommandError(
                f'Ошибка декодирования JSON "{json_file_path}".'
            )
        last_ingredient = Model.objects.order_by('-pk').first()
        next_pk = (last_ingredient.pk + 1) if last_ingredient else 1
        fixture_data = [{
            "model": model_name,
            "pk": next_pk + i,
            "fields": item
        } for i, item in enumerate(data)]
        fixture_file = 'temp_fixture.json'
        try:
            with open(fixture_file, 'w', encoding='utf-8') as outfile:
                json.dump(fixture_data, outfile, ensure_ascii=False, indent=2)
            call_command('loaddata', fixture_file)
            self.stdout.write(self.style.SUCCESS(
                'Данные успешно импортированы в модель '
                f'{model_name} из {json_file_path}'
            ))
        except Exception as e:
            raise base.CommandError(f'Ошибка импорта данных {e}')
        finally:
            import os
            try:
                os.remove(fixture_file)
            except FileNotFoundError:
                pass
