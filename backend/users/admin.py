from django.contrib.auth import get_user_model
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe


User = get_user_model()


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('avatar',)}),)
    list_display = ('username', 'email')
    list_display_links = ('username',)
    search_fields = ('email', 'username')


admin.site.register([Subscribe])
