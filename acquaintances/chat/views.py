# WEB Form
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from chat.services import get_or_create_private_chat, is_users_friends
from users.models import UserProfile
from chat.models import ChatRoom, Message
import json


@login_required
def chat_list(request):
    user = request.user

    try:
        # Получаем общий чат (создаём, если не существует)
        public_chat, created = ChatRoom.objects.get_or_create(
            is_public=True,
            defaults={'name': 'Общий чат'}
        )

        # ВСЕГДА добавляем пользователя в общий чат, если его там нет
        if user not in public_chat.participants.all():
            public_chat.participants.add(user)

        # Получаем список друзей
        friends = UserProfile.objects.filter(
            Q(friendships_initiated__to_user=user, friendships_initiated__status='accepted') |
            Q(friendships_received__from_user=user, friendships_received__status='accepted')
        ).distinct()

        private_chats = []
        for friend in friends:
            if friend == user:
                continue

            try:
                chat = get_or_create_private_chat(user, friend)
                private_chats.append(chat)
            except IntegrityError as e:
                print(f"Ошибка создания чата с {friend.username}: {e}")
                # Пропускаем проблемного друга и продолжаем
                continue

        context = {
            'public_chat': public_chat,
            'private_chats': private_chats,
        }
        return render(request, 'chat/chat_list.html', context)

    except IntegrityError as e:
        messages.error(request, "Произошла ошибка при загрузке чатов. Попробуйте обновить страницу.")
        print(f"IntegrityError в chat_list: {e}")
        return render(request, 'chat/chat_list.html', {'public_chat': None, 'private_chats': []})


@login_required
def chat_detail(request, chat_id):
    # print('\033[31mchat_detail\033[0m', chat_id)
    chat = get_object_or_404(ChatRoom, id=chat_id)
    user = request.user

    # Проверка доступа к чату
    if user not in chat.participants.all():
        messages.error(request, "У вас нет доступа к этому чату")
        return redirect('chat:chat_list')

    # Для приватных чатов проверяем дружбу
    if not chat.is_public:
        other_participants = chat.participants.exclude(id=user.id)
        for participant in other_participants:
            if not is_users_friends(user, participant):
                messages.error(request, "Вы можете общаться только с друзьями")
                return redirect('friends:friends_list')

    # Загружаем сообщения с оптимизацией запросов
    messages_list = chat.messages.select_related('sender').order_by('timestamp')

    context = {
        'chat': chat,
        'messages': messages_list,
    }
    return render(request, 'chat/chat_detail.html', context)


@login_required
def send_message(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            content = data.get('content', '').strip()

            if not content:
                return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)

            chat = get_object_or_404(ChatRoom, id=chat_id)

            # Проверка участия пользователя в чате
            if request.user not in chat.participants.all():
                return JsonResponse({'error': 'Нет доступа к чату'}, status=403)

            # Для приватных чатов проверяем дружбу с каждым участником
            if not chat.is_public:
                other_participants = chat.participants.exclude(id=request.user.id)
                for participant in other_participants:
                    if not is_users_friends(request.user, participant):
                        return JsonResponse({'error': 'Вы можете отправлять сообщения только друзьям'}, status=403)

            # Создаём сообщение
            message = Message.objects.create(
                chat_room=chat,
                sender=request.user,
                content=content
            )

            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'sender': request.user.username,
                'timestamp': message.timestamp.isoformat(),
                'formatted_time': message.timestamp.strftime('%H:%M')
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")  # Для отладки
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_new_messages(request, chat_id):
    """Возвращает новые сообщения для чата."""
    chat = get_object_or_404(ChatRoom, id=chat_id)
    user = request.user

    # Проверка доступа к чату
    if user not in chat.participants.all():
        return JsonResponse({'error': 'No access'}, status=403)

    last_id = int(request.GET.get('last_id', 0))

    # Получаем сообщения, отправленные после последнего известного ID
    new_messages = Message.objects.filter(
        chat_room=chat,
        id__gt=last_id
    ).select_related('sender').order_by('timestamp')

    messages_data = []
    for message in new_messages:
        # Рассчитываем время назад (упрощённо, можно заменить на более сложную логику)
        time_diff = timezone.now() - message.timestamp
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} дн."
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} ч."
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} мин."

        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender_username': message.sender.username,
            'is_current_user': message.sender == user,
            'time_ago': time_ago,
            'timestamp': message.timestamp.isoformat()
        })

    return JsonResponse({
        'messages': messages_data,
        'last_id': last_id,
        'chat_id': chat_id
    })
