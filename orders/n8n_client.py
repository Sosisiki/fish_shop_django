# orders/n8n_client.py
import requests
import logging
from django.conf import settings
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class N8NConsultantClient:
    def __init__(self):
        # Безопасное чтение настройки (не крашится при импорте)
        self.webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', '')
        self.timeout = getattr(settings, 'N8N_TIMEOUT', 30)

    def send_message(self, message: str, session_id: str, user_id: Optional[int] = None) -> Dict:
        if not self.webhook_url:
            logger.error("❌ N8N_WEBHOOK_URL не настроен в settings.py")
            return self._fallback()

        payload = {
            'message': message,
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # n8n может вернуть ответ в разных полях
            ai_reply = (
                result.get('message') or 
                result.get('output') or 
                result.get('text') or 
                '✅ Ответ получен'
            )
            
            return {
                'success': True,
                'message': ai_reply,
                'session_id': session_id
            }
        except requests.exceptions.Timeout:
            logger.error("⏳ Timeout при запросе к n8n")
            return self._fallback()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса к n8n: {e}")
            return self._fallback()
        except Exception as e:
            logger.exception(f"💥 Ошибка в n8n_client: {e}")
            return self._fallback()

    def _fallback(self) -> Dict:
        return {
            'success': True,
            'message': '🐠 Консультант временно обдумывает ответ. Попробуйте через минуту!',
            'session_id': 'fallback'
        }

# Глобальный экземпляр
n8n_client = N8NConsultantClient()