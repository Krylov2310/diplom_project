from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path

from friends.views import remove_friend
from .views import chat_list, chat_detail, get_new_messages, send_message

app_name = 'chat'

urlpatterns = [
                  # Чат
                  path('chats/', chat_list, name='chat_list'),
                  path('chat/<int:chat_id>/', chat_detail, name='chat_detail'),
                  path('chat/send-message/', send_message, name='send_message'),
                  re_path(r'^room/(?P<chat_id>[0-9]+)/messages/$', get_new_messages, name='get_new_messages'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
