from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import RegisterForm, EmailVerificationForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import VerificationCode
import logging

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация с явным логированием и защитой от тихих ошибок"""
    if request.user.is_authenticated:
        return redirect('products:catalog')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                # 🔹 Явно сохраняем пользователя
                user = form.save(commit=False)
                user.is_active = False  # Блокируем до ввода кода
                user.save()

                # 🔹 Генерируем код
                code_obj = VerificationCode.generate(user.email, purpose='register')

                # 🔹 Сохраняем в сессии
                request.session['verify_email'] = user.email
                request.session['verify_code_id'] = code_obj.id
                request.session['verify_purpose'] = 'register'

                logger.info(f"✅ Пользователь {user.username} ({user.email}) успешно создан в БД")
                
                # Показываем код на той же странице
                return render(request, 'accounts/register.html', {
                    'form': RegisterForm(),  # Очищаем форму
                    'verification_code': code_obj.code
                })

            except Exception as e:
                # 🔹 Ловим любые ошибки БД/сигналов
                import traceback
                logger.error(f" Ошибка при сохранении пользователя: {e}")
                traceback.print_exc()
                messages.error(request, '❌ Ошибка создания аккаунта. Проверьте логи сервера.')
        else:
            # 🔹 Выводим ошибки валидации в консоль для отладки
            logger.warning(f"⚠️ Ошибки формы регистрации: {form.errors}")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    """Страница подтверждения email кодом"""
    email = request.session.get('verify_email')
    purpose = request.session.get('verify_purpose', 'register')
    
    if not email:
        messages.warning(request, 'Сессия истекла. Начните регистрацию заново.')
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
                    id=code_id, email=email, purpose=purpose, is_used=False
                )
            except VerificationCode.DoesNotExist:
                messages.error(request, 'Код не найден или уже использован. Запросите новый.')
                return redirect('accounts:verify_email')
            
            if code_obj.is_valid() and code_obj.code == code_input:
                code_obj.is_used = True
                code_obj.save()
                
                if purpose == 'register':
                    user.is_active = True
                    user.profile.email_verified = True
                    user.profile.save()
                    user.save()
                    
                    login(request, user)
                    
                    request.session.pop('verify_email', None)
                    request.session.pop('verify_code_id', None)
                    request.session.pop('verify_purpose', None)
                    
                    messages.success(request, f'✅ Аккаунт активирован! Добро пожаловать, {user.username}!')
                    return redirect('products:catalog')
                    
                elif purpose == 'password_reset':
                    request.session['reset_confirmed'] = True
                    return redirect('accounts:password_reset_confirm')
            else:
                messages.error(request, '❌ Неверный код.')
    else:
        form = EmailVerificationForm()
    
    # 🔹 Повторная отправка кода (без проверки времени)
    if 'resend' in request.GET:
        code_obj = VerificationCode.generate(email, purpose=purpose)
        request.session['verify_code_id'] = code_obj.id
        messages.success(request, f'📋 Новый код: {code_obj.code}')
        return redirect('accounts:verify_email')

    return render(request, 'accounts/verify_email.html', {
        'form': form, 'email': email, 'purpose': purpose
    })


def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('products:catalog')
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            code_obj = VerificationCode.generate(email, purpose='password_reset')
            messages.success(request, f'✅ Код для сброса: {code_obj.code}')
            
            request.session['verify_email'] = email
            request.session['verify_code_id'] = code_obj.id
            request.session['verify_purpose'] = 'password_reset'
            return redirect('accounts:verify_email')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})


def password_reset_confirm(request):
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
                
                request.session.pop('verify_email', None)
                request.session.pop('verify_code_id', None)
                request.session.pop('verify_purpose', None)
                request.session.pop('reset_confirmed', None)
                
                messages.success(request, '✅ Пароль изменён! Войдите с новым паролем.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, 'Ошибка при обновлении пароля.')
    else:
        form = PasswordResetConfirmForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'email': email})


@login_required
def resend_verification(request):
    email = request.user.email
    code_obj = VerificationCode.generate(email, purpose='register')
    messages.info(request, f'📋 Новый код: {code_obj.code}')
    return redirect('accounts:verify_email')