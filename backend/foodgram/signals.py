from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Favorite


@receiver([post_save, post_delete], sender=Favorite)
def update_favorites_count(sender, instance, **kwargs):
    instance.recipe.favorites_count = sender.objects.filter(
        recipe=instance.recipe,
    ).count()
    instance.recipe.save()
