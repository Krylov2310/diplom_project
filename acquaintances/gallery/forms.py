from django import forms
from .models import Gallery, GalleryRating


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['image', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Добавьте комментарий к изображению...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True


class RatingForm(forms.ModelForm):
    RATING_CHOICES = [
        ('like', '❤️ Лайкнуть'),
        ('dislike', '👎 Дизлайкнуть'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Оценка'
    )

    class Meta:
        model = GalleryRating
        fields = ['rating']

    def save(self, commit=True, gallery=None, user=None):
        rating = super().save(commit=False)
        if gallery:
            rating.gallery = gallery
        if user:
            rating.user = user
        if commit:
            rating.save()
        return rating


class AddImageForms(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['comment', 'image']
        widgets = {
            'comment': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите свой комментарий к картинке'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'  # разрешаем только изображения
            })
        }
        labels = {
            'comment': 'Комментарий',
            'image': 'Выберите изображение'
        }