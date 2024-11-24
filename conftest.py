# conftest.py
import os
import django
from django.conf import settings

def pytest_configure():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ai_news.test_settings'
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
    django.setup()
