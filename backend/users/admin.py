from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import Subscribe


User = get_user_model()


class RelatedObjectsFilter(admin.SimpleListFilter):
    related_name = None
    title = None

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(
                **{f'{self.related_name}__isnull': False}
            ).distinct()
        return users.filter(**{f'{self.related_name}__isnull': True})


class HasRecipesFilter(RelatedObjectsFilter):
    title = 'Имеет рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(RelatedObjectsFilter):
    title = 'Имеет подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscribers'


class HasFollowersFilter(RelatedObjectsFilter):
    title = 'Имеет подписчиков'
    parameter_name = 'has_subscribers'
    related_name = 'authors'


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('avatar',)}),)
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_thumbnail',
        'recipe_count', 'subscriber_count', 'author_count'
    )
    list_display_links = ('username',)
    search_fields = ('email', 'username')
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}"

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_thumbnail(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="40" height="40" />'
        return 'Нет аватара'

    @admin.display(description='Кол-во рецептов')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Кол-во подписок')
    def subscriber_count(self, user):
        return user.subscribers.count()

    @admin.display(description='Кол-во подписчиков')
    def author_count(self, user):
        return user.authors.count()

@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')
