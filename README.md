# 🐟 Fish Shop Django

Полноценный интернет-магазин на Django, разработанный в рамках учебной/производственной практики. Проект включает в себя каталог товаров, систему заказов, авторизацию пользователей и интеграцию с внешними сервисами.

## 🛠 Стек технологий
- **Backend:** Python, Django, Django REST Framework
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **База данных:** SQLite (с возможностью миграции на PostgreSQL)
- **Деплой:** Render (конфигурация `render.yaml` включена)
- **Дополнительно:** Интеграция с email-сервисом (Resend) для уведомлений

## 🚀 Функционал
- Регистрация и аутентификация пользователей.
- Каталог товаров с категориями.
- Корзина и оформление заказов.
- Генерация отчетов (скрипт `create_report.py`).

## ⚙️ Как запустить локально

Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Sosisiki/fish_shop_django.git
   cd fish_shop_django
Создайте виртуальное окружение и установите зависимости:
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   pip install -r requirements.txt
Примените миграции и создайте суперпользователя:
     python manage.py migrate
   python manage.py createsuperuser
Запустите сервер разработки:
   python manage.py runserver


   Структура проекта
accounts/ - управление пользователями и аутентификация.
products/ - каталог товаров и категории.
orders/ - логика корзины и оформления заказов.
config/ - основные настройки Django проекта.
   
