from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from chat.services import get_or_create_private_chat
from .models import Friendship
from users.models import UserProfile
from django.db import transaction
from chat.models import ChatRoom


# Отправка заявки в друзья:
@login_required
def send_friend_request(request, user_id):
    target_user = get_object_or_404(UserProfile, id=user_id)
    success, message = request.user.send_friend_request(target_user)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    # Получаем профиль пользователя для передачи в контекст
    profile_user = target_user
    is_friend = request.user.is_friend(profile_user)

    context = {
        'profile_user': profile_user,
        'is_friend': is_friend,
    }
    return render(request, 'users/profile_detail.html', context)


# Подтверждение/отклонение заявки:
@login_required
def manage_friend_request(request, friendship_id, action):
    friendship = get_object_or_404(Friendship, id=friendship_id)

    if action == 'accept':
        success, message = request.user.accept_friend_request(friendship.from_user)
        if success:
            try:
                # Используем атомарный метод
                chat = get_or_create_private_chat(request.user, friendship.from_user)
                messages.success(request, f"{message} Чат создан: {chat.name}")
            except Exception as e:
                messages.error(request, f"{message}. Ошибка создания чата: {str(e)}")
    elif action == 'reject':
        success, message = request.user.reject_friend_request(friendship.from_user)
    else:
        messages.error(request, "Неверное действие")
        return redirect('/friend/requests/')

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('/friend/requests/')


# Просмотр списка друзей:
@login_required
def friends_list(request):
    friends = request.user.get_friends()
    return render(request, 'friends/friends_list.html', {'friends': friends})


# Просмотр входящих заявок:
@login_required
def friend_requests(request):
    pending_requests = request.user.get_pending_friend_requests()
    return render(request, 'friends/friend_requests.html', {
        'pending_requests': pending_requests
    })


@login_required
def remove_friend(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(UserProfile, id=user_id)

        with transaction.atomic():
            # Сначала удаляем дружбу
            success, message = request.user.remove_from_friends(target_user)

            if success:
                # Удаляем приватные чаты между пользователями
                chats_to_delete = ChatRoom.objects.filter(
                    is_public=False,
                    participants=request.user
                ).filter(
                    participants=target_user
                ).annotate(
                    participant_count=Count('participants')
                ).filter(participant_count=2)

                deleted_count = chats_to_delete.count()
                chats_to_delete.delete()

                # Формируем итоговое сообщение
                if deleted_count > 0:
                    message += f" | Удалено {deleted_count} приватных чатов"

        return JsonResponse({'success': success, 'message': message})

    return JsonResponse({'success': False, 'message': 'Invalid request'})
