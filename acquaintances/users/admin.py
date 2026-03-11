from django.contrib import admin
from .models import UserProfile
from django.contrib.auth.admin import UserAdmin


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    def __str__(self):
        avatar_info = f", аватар: {self.avatar_gallery_image}" if self.avatar_gallery_image else ""
        return f"{self.email}{avatar_info}"

    list_display = (
        'email', 'username', 'first_name', 'last_name',
        'birth_year'
    )
    list_filter = (
        'gender', 'is_staff', 'is_superuser', 'is_active',
        'date_joined', 'last_login', 'birth_year'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': (
                'username', 'first_name', 'last_name', 'patronymic',
                'avatar_gallery_image', 'gender', 'age', 'city', 'hobbies', 'status', 'birth_year'
            )
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('gallery_ratings', 'galleries')  # 'galleries'


# Настройка заголовка админки
admin.site.site_header = 'Админка системы профилей пользователей'
admin.site.site_title = 'Система профилей пользователей'
admin.site.index_title = 'Панель управления'
