from django.conf import settings
from django.db import models
from users.utils import user_directory_path_gallery


# Модель галереи
class Gallery(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='galleries'
    )
    image = models.ImageField(upload_to=user_directory_path_gallery, blank=True, null=True)
    comment = models.CharField('Комментарий', null=True, blank=True)

    # Добавляем поле created_at
    created_at = models.DateTimeField(auto_now_add=True)  # Автоматически устанавливается при создании

    # Счётчики лайков и дизлайков для галереи
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Галерея'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return f'{self.image}: {self.comment}: {self.author}'


class GalleryRating(models.Model):
    """Модель для хранения оценок (лайков/дизлайков) галереи пользователями"""
    LIKE = 'like'
    DISLIKE = 'dislike'

    RATING_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gallery_ratings'
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        default=LIKE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('gallery', 'user')  # Один пользователь — одна оценка
        verbose_name = 'Оценка галереи'
        verbose_name_plural = 'Оценки галереи'

    def __str__(self):
        return f'{self.user} оценил {self.gallery} как {self.get_rating_display()}'

    def update_ratings_count(self):
        """Обновляет счётчики лайков и дизлайков для галереи"""
        likes = self.ratings.filter(rating='like').count()
        dislikes = self.ratings.filter(rating='dislike').count()

        self.likes_count = likes
        self.dislikes_count = dislikes
        self.save()

    def get_user_rating(self, user):
        """Возвращает оценку пользователя для этой галереи, если есть"""
        try:
            rating = self.ratings.get(user=user)
            return rating.rating
        except GalleryRating.DoesNotExist:
            return None

    def update_rating_stats(self):
        """Обновляет статистику оценок для пользователя"""
        # Оценки, которые поставил пользователь
        ratings_given = self.gallery_ratings.count()

        # Лайки и дизлайки, полученные для галерей пользователя
        galleries = Gallery.objects.filter(author=self)
        total_likes = 0
        total_dislikes = 0

        for gallery in galleries:
            total_likes += gallery.likes_count
            total_dislikes += gallery.dislikes_count

        self.total_ratings_given = ratings_given
        self.total_likes_received = total_likes
        self.total_dislikes_received = total_dislikes
        self.save()
