import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(__file__)) 

# Указываем Django, какой файл настроек использовать
os.environ['DJANGO_SETTINGS_MODULE'] = 'MBBmatan.settings'

# Запускаем WSGI-приложение
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()