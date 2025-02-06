from django.apps import AppConfig


class FoodgramConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'foodgram'

    def ready(self):
        import foodgram.signals
        foodgram.signals
