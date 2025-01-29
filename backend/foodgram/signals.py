from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Favorites


@receiver(post_save, sender=Favorites)
def update_favorites_count(sender, instance, created, **kwargs):
    instance.recipe.favorites_count = sender.objects.filter(
        recipe=instance.recipe,
        is_favorited=True
    ).count()
    instance.recipe.save()

