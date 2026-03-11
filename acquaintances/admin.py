from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from users.admin import UserProfileAdmin
from users.models import UserProfile


class CustomAdminSite(AdminSite):
    site_header = _('Админка системы профилей')
    site_title = _('Система профилей')
    index_title = _('Главная панель')

    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        context['index_title'] = self.index_title
        return context


# Регистрируем кастомную админку (если нужно)
admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(UserProfile, UserProfileAdmin)
