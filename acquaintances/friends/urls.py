from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from friends.views import send_friend_request, manage_friend_request, friends_list, friend_requests, remove_friend

app_name = 'friends'

urlpatterns = [
                  # Друзья
                  path('friend/request/<int:user_id>/', send_friend_request, name='send_friend_request'),
                  path('friend/manage/<int:friendship_id>/<str:action>/', manage_friend_request,
                       name='manage_friend_request'),
                  path('friends/', friends_list, name='friends_list'),
                  path('friend/requests/', friend_requests, name='friend_requests'),
                  path('friend/remove/<int:user_id>/', remove_friend, name='remove_friend'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
