from django.shortcuts import redirect

class EmailVerificationMiddleware:
    """Блокирует доступ к покупке для пользователей с неподтверждённым email"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = {
            '/accounts/login/',
            '/accounts/register/',
            '/accounts/verify-email/',
            '/accounts/resend-verification/',
            '/accounts/password-reset/',
            '/accounts/password-reset/confirm/',
            '/accounts/logout/',
            '/catalog/',
            '/about/',
            '/support/',
            '/delivery/',
            '/returns/',
            '/guarantee/',
            '/admin/',
            '/static/',
            '/media/',
        }

    def __call__(self, request):
        response = self.get_response(request)
        
        if not request.user.is_authenticated or request.user.is_staff:
            return response
        
        path = request.path.rstrip('/')
        
        if f"{path}/" in self.exempt_paths or path.startswith('/static') or path.startswith('/media') or path == '':
            return response
        
        # 🔒 Блокируем, если email не подтверждён
        if not request.user.profile.email_verified:
            return redirect('accounts:verify_email')
        
        return response