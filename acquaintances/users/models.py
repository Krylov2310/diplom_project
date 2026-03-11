from datetime import datetime
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

from friends.models import Friendship
from gallery.models import Gallery


def get_birth_year_choices():
    """Генерирует варианты выбора для года рождения"""
    current_year = datetime.now().year
    min_year = current_year - 100
    max_year = current_year - 18
    # Создаём варианты: (год, строка_года), плюс опция «Не выбран»
    choices = [(None, 'Не выбран')] + [
        (year, str(year)) for year in range(max_year, min_year - 1, -1)
    ]
    return choices


def user_directory_path_avatar(instance, filename):
    # print('user_directory_path', instance.id, filename)
    if instance.id:
        username = instance.id
    else:
        # Генерируем уникальный идентификатор, если user не назначен
        username = f'unknown_{uuid.uuid4().hex[:8]}'
    return f'images/{username}/{filename}'


class UserProfile(AbstractUser):
    NONE = '-'
    MALE = 'M'
    FEMALE = 'F'

    GENDER_CHOICES = (
        (NONE, '-'),
        (MALE, 'Мужской'),
        (FEMALE, 'Женский'),
    )
    CURRENT_YEAR = datetime.now().year

    patronymic = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, blank=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='-')
    age = models.IntegerField(validators=[MinValueValidator(0)], blank=True, null=True)
    avatar_gallery_image = models.ForeignKey(
        'gallery.Gallery',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='used_as_avatar',
        verbose_name='Аватар из галереи'
    )
    city = models.CharField(max_length=150, blank=True)
    hobbies = models.TextField(blank=True)
    status = models.CharField(max_length=50, blank=True)
    privacy_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Настройки приватности',
        help_text='Словарь настроек приватности, включая список друзей'
    )

    # Поле для года рождения с динамическими choices
    birth_year = models.IntegerField(
        choices=get_birth_year_choices(),  # Вызываем функцию здесь
        null=True,
        blank=True,
        help_text=f"Год рождения (от {datetime.now().year - 100} до {datetime.now().year - 18})"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Переопределяем метод save для автоматической установки возраста и обработки аватара"""
        if self.birth_year:
            current_year = datetime.now().year
            self.age = current_year - self.birth_year
        else:
            self.age = None

        # Если выбран аватар из галереи, берём его изображение
        if self.avatar_gallery_image and self.avatar_gallery_image.image:
            # Здесь можно добавить логику копирования изображения в отдельное поле, если требуется
            pass  # На данном этапе просто сохраняем ссылку

        super().save(*args, **kwargs)

    # Аватар из галереи
    def get_avatar_url(self):
        """Возвращает URL аватара: из галереи или дефолтное изображение"""
        if self.avatar_gallery_image and self.avatar_gallery_image.image:
            return self.avatar_gallery_image.image.url
        else:
            # Возвращаем дефолтное изображение, если аватар не выбран
            return '/static/images/default-avatar.png'

    # Статус оценок
    def update_rating_stats(self):
        """Обновляет статистику оценок для пользователя"""
        # Оценки, которые поставил пользователь (через gallery_ratings_given)
        ratings_given = self.gallery_ratings_given.count()

        # Лайки и дизлайки, полученные для галерей пользователя
        galleries = Gallery.objects.filter(author=self)
        total_likes = 0
        total_dislikes = 0

        for gallery in galleries:
            total_likes += gallery.gallery_ratings.filter(rating='like').count()
            total_dislikes += gallery.gallery_ratings.filter(rating='dislike').count()

        self.total_ratings_given = ratings_given
        self.total_likes_received = total_likes
        self.total_dislikes_received = total_dislikes
        self.save()

    # Отправка заявки в друзья:
    def send_friend_request(self, target_user):
        """Отправляет заявку в друзья"""
        if self == target_user:
            return False, "Нельзя добавить себя в друзья"

        # Проверяем, нет ли уже существующей записи
        existing = Friendship.objects.filter(
            from_user=self,
            to_user=target_user
        ).first()

        if existing:
            if existing.status == 'accepted':
                return False, "Вы уже друзья"
            elif existing.status == 'pending':
                return False, "Заявка уже отправлена"
            else:  # rejected
                existing.status = 'pending'
                existing.save()
                return True, "Заявка отправлена повторно"
        else:
            Friendship.objects.create(
                from_user=self,
                to_user=target_user,
                status='pending'
            )
            return True, "Заявка в друзья отправлена"

    # Подтверждение заявки:
    # def accept_friend_request(self, requester_user):
    #     """Подтверждает заявку в друзья"""
    #     friendship = Friendship.objects.filter(
    #         from_user=requester_user,
    #         to_user=self,
    #         status='pending'
    #     ).first()
    #
    #     if friendship:
    #         friendship.status = 'accepted'
    #         friendship.save()
    #         return True, "Дружба подтверждена"
    #     return False, "Заявка не найдена"

    def accept_friend_request(self, from_user):
        """Принимает заявку в друзья и создаёт чат."""
        try:
            friendship = Friendship.objects.get(
                from_user=from_user,
                to_user=self,
                status='pending'
            )
            friendship.status = 'accepted'
            friendship.save()

            # Создаём чат после принятия дружбы
            self.create_or_get_private_chat(from_user)

            return True, f"Вы приняли заявку от {from_user.username}. Чат создан!"
        except Friendship.DoesNotExist:
            return False, "Заявка не найдена"

    # Отклонение заявки:
    def reject_friend_request(self, requester_user):
        """Отклоняет заявку в друзья"""
        friendship = Friendship.objects.filter(
            from_user=requester_user,
            to_user=self,
            status='pending'
        ).first()

        if friendship:
            friendship.status = 'rejected'
            friendship.save()
            return True, "Заявка отклонена"
        return False, "Заявка не найдена"

    # Удаление из друзей:
    def remove_from_friends(self, friend_user):
        """Удаляет пользователя из друзей"""
        # Удаляем обе стороны дружбы
        Friendship.objects.filter(
            (models.Q(from_user=self, to_user=friend_user) |
             models.Q(from_user=friend_user, to_user=self)),
            status='accepted'
        ).delete()
        return True, "Пользователь удалён из друзей"

    # Проверка дружбы:
    def is_friend(self, user):
        """Проверяет, является ли пользователь другом"""
        return Friendship.objects.filter(
            models.Q(from_user=self, to_user=user, status='accepted') |
            models.Q(from_user=user, to_user=self, status='accepted')
        ).exists()

    #  Получение списка друзей:
    def get_friends(self):
        """Возвращает QuerySet пользователей‑друзей"""
        friends_ids = Friendship.objects.filter(
            models.Q(from_user=self, status='accepted') |
            models.Q(to_user=self, status='accepted')
        ).values_list('from_user_id', 'to_user_id')

        friend_ids = set()
        for from_id, to_id in friends_ids:
            if from_id != self.id:
                friend_ids.add(from_id)
            if to_id != self.id:
                friend_ids.add(to_id)

        return UserProfile.objects.filter(id__in=friend_ids).exclude(id=self.id)

    # Получение входящих заявок:
    def get_pending_friend_requests(self):
        """Возвращает входящие заявки в друзья"""
        return Friendship.objects.filter(
            to_user=self,
            status='pending'
        )

    # Получение чата с другим пользователем:
    def get_private_chat(self, other_user):
        """Возвращает приватный чат с другим пользователем или создаёт новый"""
        from chat.models import ChatRoom
        # Ищем чат, где участвуют оба пользователя и только они
        chats = ChatRoom.objects.filter(participants=self).filter(participants=other_user)
        chats = chats.annotate(num_participants=models.Count('participants'))
        chats = chats.filter(num_participants=2)

        if chats.exists():
            return chats.first()

        # Создаём новый чат
        chat = ChatRoom.objects.create()
        chat.participants.add(self, other_user)
        return chat

    # Формирование единого ID для чата:
    def create_or_get_private_chat(self, other_user):
        from django.db.models import Count
        from chat.models import ChatRoom
        """Создаёт или получает существующий приватный чат между двумя пользователями."""
        # Ищем чат с ровно двумя участниками: self и other_user
        chat = ChatRoom.objects.filter(
            is_public=False
        ).filter(
            participants=self
        ).filter(
            participants=other_user
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()

        if not chat:
            # Создаём новый чат
            chat = ChatRoom.objects.create(
                name=f"Чат с {other_user.username}"
            )
            chat.participants.add(self, other_user)

        return chat

    def get_chats(self):
        from chat.models import ChatRoom  # Ленивый импорт
        return ChatRoom.objects.filter(participants=self).prefetch_related('participants').distinct()

    # Получение последних сообщений для списка чатов:
    def get_last_messages(self):
        """Возвращает последние сообщения для каждого чата пользователя"""
        chats = self.get_chats()
        last_messages = {}

        for chat in chats:
            last_msg = chat.messages.order_by('-timestamp').first()
            last_messages[chat.id] = last_msg

        return last_messages


class GalleryRating(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'

    RATING_CHOICES = [
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    ]

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='gallery_ratings_given',  # Уникальное имя
        verbose_name='Пользователь'
    )
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='gallery_ratings',  # Уникальное имя
        verbose_name='Галерея'
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        verbose_name='Тип оценки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        unique_together = ('user', 'gallery')
        verbose_name = 'Оценка галереи'
        verbose_name_plural = 'Оценки галерей'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating} - {self.gallery.id}"
