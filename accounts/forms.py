from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import Profile

# ✅ Список разрешённых российских доменов
RUSSIAN_EMAIL_DOMAINS = [
    'mail.ru', 'yandex.ru', 'bk.ru', 'inbox.ru', 
    'list.ru', 'rambler.ru', 'proton.me', 'protonmail.com'
]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru',
            'autocomplete': 'email'
        }),
        help_text="Разрешены только российские почтовые сервисы: mail.ru, yandex.ru, bk.ru, inbox.ru, list.ru, rambler.ru, proton.me"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Логин',
            'autocomplete': 'username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # ✅ Проверка: только российские домены
        domain = email.split('@')[-1] if '@' in email else ''
        if domain not in RUSSIAN_EMAIL_DOMAINS:
            raise forms.ValidationError(
                f"Разрешены только российские почтовые сервисы: {', '.join(RUSSIAN_EMAIL_DOMAINS)}"
            )
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.is_active = False  # Не активен до подтверждения
        if commit:
            user.save()
            profile = user.profile
            profile.email_verified = False
            profile.save()
        return user


class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••••',
            'maxlength': '6',
            'style': 'letter-spacing: 8px; font-size: 1.5rem;',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'one-time-code'
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Код должен состоять из 6 цифр")
        return code


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru',
            'autocomplete': 'email'
        }),
        help_text="Введите email, указанный при регистрации (только российские домены)"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # ✅ Проверка домена и для сброса пароля
        domain = email.split('@')[-1] if '@' in email else ''
        if domain not in RUSSIAN_EMAIL_DOMAINS:
            raise forms.ValidationError(
                f"Разрешены только российские почтовые сервисы: {', '.join(RUSSIAN_EMAIL_DOMAINS)}"
            )
        
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Если такой аккаунт существует, код будет показан")
        return email


class PasswordResetConfirmForm(forms.Form):
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '••••••',
            'maxlength': '6',
            'style': 'letter-spacing: 8px; font-size: 1.5rem;',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code'
        })
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль',
            'autocomplete': 'new-password'
        })
    )
    new_password2 = forms.CharField(
        label="Повторите новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password'
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Код должен состоять из 6 цифр")
        return code

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2