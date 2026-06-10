import requests
import logging
from django.conf import settings
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class N8NConsultantClient:
    def __init__(self):
        # Читаем настройки при каждом вызове (а не при импорте),
        # чтобы изменения в settings.py подхватывались без перезапуска
        pass

    @property
    def webhook_url(self):
        return getattr(settings, 'N8N_WEBHOOK_URL', '')

    @property
    def timeout(self):
        return getattr(settings, 'N8N_TIMEOUT', 25)

    def send_message(self, message: str, session_id: str, user_id: Optional[int] = None) -> Dict:
        # 🔹 Проверка: URL настроен
        if not self.webhook_url:
            logger.error("❌ N8N_WEBHOOK_URL не настроен в settings.py")
            return self._fallback("Сервис консультанта не настроен")

        # 🔹 Проверка: сообщение не пустое
        if not message or not message.strip():
            return {
                'success': False,
                'message': 'Сообщение не может быть пустым',
                'session_id': session_id
            }

        payload = {
            'message': message.strip(),
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()

            # 🔹 Безопасный парсинг JSON (n8n может вернуть не JSON)
            try:
                result = response.json()
            except ValueError:
                logger.warning(f"⚠️ n8n вернул не-JSON ответ: {response.text[:200]}")
                result = {'message': response.text}

            # n8n может вернуть ответ в разных полях
            ai_reply = (
                result.get('message') or
                result.get('output') or
                result.get('text') or
                result.get('response') or
                '✅ Ответ получен'
            )

            return {
                'success': True,
                'message': ai_reply,
                'session_id': session_id
            }

        except requests.exceptions.Timeout:
            logger.error(f"⏳ Timeout ({self.timeout}s) при запросе к n8n")
            return self._fallback("Консультант думает слишком долго. Попробуйте ещё раз.")

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP ошибка от n8n: {e.response.status_code} - {e.response.text[:200]}")
            return self._fallback("Сервис консультанта временно недоступен")

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Нет соединения с n8n: {self.webhook_url}")
            return self._fallback("Нет связи с сервисом консультанта")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запроса к n8n: {e}")
            return self._fallback("Ошибка соединения с консультантом")

        except Exception as e:
            logger.exception(f"💥 Непредвиденная ошибка в n8n_client: {e}")
            return self._fallback("Произошла ошибка. Попробуйте позже.")

    def _fallback(self, reason: str = "Сервис временно недоступен") -> Dict:
        """Возвращаем success=False, чтобы фронтенд показал это как ошибку"""
        return {
            'success': False,
            'message': f'🐠 {reason}',
            'session_id': 'fallback'
        }


# Глобальный экземпляр
n8n_client = N8NConsultantClient()