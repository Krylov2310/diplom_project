from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from users.views import index, info, login_view, register, user_logout, profile_edit, profile_detail, \
    edit_password, profile_list_view

app_name = 'users'

urlpatterns = [
                  # Веб‑интерфейс
                  path('', index, name='index'),
                  path('info/', info, name='info'),
                  # Аутентификация
                  path('login/', login_view, name='login'),
                  path('register/', register, name='register'),
                  path('logout/', user_logout, name='logout'),
                  path('profile/edit/<int:user_id>/', profile_edit, name='profile_edit'),
                  path('profile/pass/', edit_password, name='edit_password'),
                  path('profile/<int:user_id>/', profile_detail, name='profile_detail'),
                  path('profile/list/', profile_list_view, name='profile_list'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
