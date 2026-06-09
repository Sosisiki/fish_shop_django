import os
import sys

# Путь к проекту на Beget (замени username на свой логин!)
sys.path.insert(0, '/home/u123456789/fish_shop_django')
sys.path.insert(0, '/home/u123456789/fish_shop_django/venv/lib/python3.11/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()