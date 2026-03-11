from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from django.contrib.auth import authenticate

from gallery.models import Gallery
from .models import UserProfile


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Неверные учётные данные',
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ('email', 'username', 'first_name', 'last_name')


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'patronymic', 'username', 'gender', 'age', 'email', 'avatar_gallery_image']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя'
            }),
            'patronymic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Отчество'
            }),
            'gender': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пол'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Возраст'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@domain.com'
            }),
            'avatar_gallery_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'patronymic': 'Отчество',
            'username': 'Имя пользователя',
            'gender': 'Пол',
            'age': 'Возраст',
            'email': 'Email',
            'avatar_gallery_image': 'Аватар'
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserProfile.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Это имя пользователя уже занято.')
        return username


class PasswordChangeForm(SetPasswordForm):
    old_password = forms.CharField(
        label='Старый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Неверный старый пароль.')
        return old_password


class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not old_password:
            raise forms.ValidationError('Старый пароль обязателен для заполнения.')
        # Проверяем, что старый пароль корректен
        user = authenticate(username=self.user.username, password=old_password)
        if user is None:
            raise forms.ValidationError('Введённый старый пароль неверен.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('Новые пароли не совпадают.')
        if not new_password1:
            raise forms.ValidationError('Новый пароль обязателен для заполнения.')

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    avatar_gallery_image = forms.ModelChoiceField(
        queryset=Gallery.objects.none(),  # Заполним в __init__
        required=False,
        label='Аватар из галереи',
        empty_label='Использовать стандартное изображение'
    )

    class Meta:
        model = UserProfile
        fields = [
            'username', 'first_name', 'last_name', 'patronymic',
            'email', 'gender', 'birth_year', 'city', 'hobbies', 'status'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Фильтруем только изображения текущего пользователя
            self.fields['avatar_gallery_image'].queryset = Gallery.objects.filter(
                author=self.instance
            )
