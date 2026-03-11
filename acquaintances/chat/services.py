import hashlib
from django.db import transaction
from chat.models import ChatRoom
from django.db.models import Count, Q


@transaction.atomic
def get_or_create_private_chat(user1, user2):
    """
    Получает или создаёт приватный чат между двумя пользователями с единым ID.
    Гарантирует, что для пары пользователей существует только один чат.
    """
    if user1 == user2:
        raise ValueError("Cannot create private chat with oneself")

    # Сначала ищем существующий чат
    existing_chat = ChatRoom.objects.filter(
        is_public=False,
        private_chat_id__isnull=False
    ).filter(
        participants=user1
    ).filter(
        participants=user2
    ).annotate(
        participant_count=Count('participants')
    ).filter(participant_count=2).first()

    if existing_chat:
        return existing_chat

    # Генерируем ID заранее
    sorted_ids = sorted([user1.id, user2.id])
    chat_string = f"{sorted_ids[0]}:{sorted_ids[1]}"
    proposed_chat_id = hashlib.sha256(chat_string.encode()).hexdigest()

    # Проверяем, не существует ли чат с таким ID
    conflict_chat = ChatRoom.objects.filter(private_chat_id=proposed_chat_id).first()
    if conflict_chat:
        # Проверяем участников конфликта
        if set(conflict_chat.participants.all()) == {user1, user2}:
            return conflict_chat
        else:
            # Конфликт ID, но другие участники — генерируем новый ID
            proposed_chat_id = f"{proposed_chat_id}_{user1.id}_{user2.id}"
    if user1.first_name and user2.first_name:
        # Создаём новый чат
        chat = ChatRoom.objects.create(
            name=f"{user1.first_name} & {user2.first_name}",
            is_public=False,
            private_chat_id=proposed_chat_id
        )
    else:
        # Создаём новый чат
        chat = ChatRoom.objects.create(
            name=f"{user1.username} & {user2.username}",
            is_public=False,
            private_chat_id=proposed_chat_id
        )

    # Добавляем участников
    chat.participants.add(user1, user2)

    return chat


def delete_private_chat_if_needed(user1, user2):
    """
    Удаляет приватный чат между двумя пользователями, если они больше не друзья.
    """
    # Ищем приватный чат ровно с двумя участниками
    chat = ChatRoom.objects.filter(
        is_public=False,
        private_chat_id__isnull=False
    ).filter(
        participants=user1
    ).filter(
        participants=user2
    ).annotate(
        participant_count=Count('participants')
    ).filter(participant_count=2).first()

    if chat:
        # Проверяем, остались ли пользователи друзьями
        from friends.models import Friendship

        are_still_friends = Friendship.objects.filter(
            Q(from_user=user1, to_user=user2, status='accepted') |
            Q(from_user=user2, to_user=user1, status='accepted')
        ).exists()

        if not are_still_friends:
            # Удаляем чат и все связанные сообщения (благодаря on_delete=models.CASCADE)
            chat.delete()
            return True  # Чат удалён

    return False  # Чат не найден или пользователи всё ещё друзья


def is_users_friends(user1, user2):
    """Проверяет, являются ли два пользователя друзьями."""
    from friends.models import Friendship
    if user1 == user2:
        return False
    return Friendship.objects.filter(
        from_user=user1, to_user=user2, status='accepted'
    ).exists() or Friendship.objects.filter(
        from_user=user2, to_user=user1, status='accepted'
    ).exists()