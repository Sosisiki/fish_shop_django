from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, VerificationCode, PasswordResetToken

# Inline-редактирование профиля прямо в карточке пользователя
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('email_verified', 'created_at')
    readonly_fields = ('created_at',)


class UserAdmin(BaseUserAdmin):
    """Расширенная админка пользователя с отображением статуса email"""
    inlines = (ProfileInline,)
    
    # Показываем email и статус в списке пользователей
    list_display = ('username', 'email', 'get_email_status', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'profile__email_verified', 'date_joined')
    search_fields = ('username', 'email')
    
    def get_email_status(self, obj):
        """Показывает статус подтверждения email"""
        if hasattr(obj, 'profile') and obj.profile.email_verified:
            return '✅ Подтверждён'
        return '❌ Не подтверждён'
    get_email_status.short_description = 'Email'
    get_email_status.admin_order_field = 'profile__email_verified'


# Перерегистрируем User с нашей кастомной админкой
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'purpose', 'created_at', 'is_used', 'is_valid_admin')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('email', 'code')
    readonly_fields = ('email', 'code', 'purpose', 'created_at', 'is_used')
    
    def is_valid_admin(self, obj):
        """Показывает, действителен ли код сейчас"""
        return obj.is_valid()
    is_valid_admin.short_description = 'Действителен'
    is_valid_admin.boolean = True


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'is_used', 'is_valid_admin')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('user', 'token', 'created_at', 'is_used')
    
    def is_valid_admin(self, obj):
        """Показывает, действителен ли токен сейчас"""
        return obj.is_valid()
    is_valid_admin.short_description = 'Действителен'
    is_valid_admin.boolean = True