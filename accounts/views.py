from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from .forms import RegisterForm, EmailVerificationForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import Profile, VerificationCode
import logging

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация: показ кода прямо на странице (без отправки email)"""
    verification_code = None
    
    if request.user.is_authenticated:
        return redirect('products:catalog')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Блокируем до верификации
            user.save()
            
            # Генерируем код
            code_obj = VerificationCode.generate(user.email, purpose='register')
            verification_code = code_obj.code  # ✅ Сохраняем код для показа на странице
            
            # 🔹 НЕ отправляем письмо — код показываем прямо на странице
            # (отправка отключена для демо, чтобы не зависеть от внешних сервисов)
            
            # Сохраняем в сессии для проверки
            request.session['verify_email'] = user.email
            request.session['verify_code_id'] = code_obj.id
            request.session['verify_purpose'] = 'register'
            
            messages.success(request, f'✅ Регистрация начата! Ваш код: {verification_code}')
            # ✅ Возвращаем тот же шаблон с кодом, а не редирект
            return render(request, 'accounts/register.html', {
                'form': RegisterForm(),  # Очищаем форму
                'verification_code': verification_code  # ✅ Передаём код в шаблон
            })
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    """Страница подтверждения email кодом"""
    email = request.session.get('verify_email')
    purpose = request.session.get('verify_purpose', 'register')
    
    if not email:
        messages.warning(request, 'Сессия истекла. Пожалуйста, начните регистрацию заново.')
        return redirect('accounts:register')
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('accounts:register')
    
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            code_input = form.cleaned_data['code']
            code_id = request.session.get('verify_code_id')
            
            try:
                code_obj = VerificationCode.objects.get(
                    id=code_id,
                    email=email,
                    purpose=purpose,
                    is_used=False
                )
            except VerificationCode.DoesNotExist:
                messages.error(request, 'Код не найден или уже использован. Запросите новый.')
                return redirect('accounts:verify_email')
            
            if code_obj.is_valid() and code_obj.code == code_input:
                # ✅ Подтверждаем email
                code_obj.is_used = True
                code_obj.save()
                
                if purpose == 'register':
                    # Активируем аккаунт
                    user.is_active = True
                    user.profile.email_verified = True
                    user.profile.save()
                    user.save()
                    
                    # Автоматический вход
                    login(request, user)
                    
                    # Очищаем сессию
                    request.session.pop('verify_email', None)
                    request.session.pop('verify_code_id', None)
                    request.session.pop('verify_purpose', None)
                    
                    messages.success(request, f'✅ Email подтверждён! Добро пожаловать, {user.username}!')
                    return redirect('products:catalog')
                    
                elif purpose == 'password_reset':
                    # Переходим к установке нового пароля
                    request.session['reset_confirmed'] = True
                    return redirect('accounts:password_reset_confirm')
            else:
                messages.error(request, '❌ Неверный код или время действия истекло.')
    else:
        form = EmailVerificationForm()
    
    # Повторная генерация кода (без отправки)
    if 'resend' in request.GET:
        code_obj = VerificationCode.generate(email, purpose=purpose)
        messages.info(request, f'📋 Новый код: {code_obj.code}')
        request.session['verify_code_id'] = code_obj.id
        return redirect('accounts:verify_email')

    return render(request, 'accounts/verify_email.html', {
        'form': form,
        'email': email,
        'purpose': purpose
    })


def password_reset_request(request):
    """Запрос на сброс пароля: показ кода прямо на странице"""
    if request.user.is_authenticated:
        return redirect('products:catalog')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            
            # Генерируем код
            code_obj = VerificationCode.generate(email, purpose='password_reset')
            
            # 🔹 Показываем код в сообщении (без отправки)
            messages.success(request, f'✅ Код для сброса пароля: {code_obj.code}')
            
            # Сохраняем в сессии
            request.session['verify_email'] = email
            request.session['verify_code_id'] = code_obj.id
            request.session['verify_purpose'] = 'password_reset'
            
            return redirect('accounts:verify_email')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})


def password_reset_confirm(request):
    """Установка нового пароля после подтверждения кода"""
    if not request.session.get('reset_confirmed'):
        messages.warning(request, 'Сначала подтвердите код.')
        return redirect('accounts:password_reset_request')
    
    email = request.session.get('verify_email')
    if not email:
        return redirect('accounts:password_reset_request')
    
    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password2']
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Очищаем сессию
                request.session.pop('verify_email', None)
                request.session.pop('verify_code_id', None)
                request.session.pop('verify_purpose', None)
                request.session.pop('reset_confirmed', None)
                
                messages.success(request, '✅ Пароль успешно изменён! Теперь можно войти.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, 'Ошибка при обновлении пароля.')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'email': email})


@login_required
def resend_verification(request):
    """Повторная генерация кода (без отправки)"""
    email = request.user.email
    code_obj = VerificationCode.generate(email, purpose='register')
    
    messages.info(request, f'📋 Ваш новый код: {code_obj.code}')
    return redirect('accounts:verify_email')