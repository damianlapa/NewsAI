import os
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from articles.models import Category, UserProfile

# Wykorzystanie test_settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ai_news.test_settings'
override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)

class SettingsUITests(TestCase):
    def setUp(self):
        # Wyczyść bazę danych przed każdym testem
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Category.objects.all().delete()

        # Utwórz użytkownika
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Użyj get_or_create zamiast create
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)

        # Utwórz kategorię i zaloguj użytkownika
        self.category = Category.objects.create(name='AI')
        self.client.login(username='testuser', password='testpass123')

    def test_settings_page_accessibility(self):
        """Test dostępności strony ustawień"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        # Sprawdź czy strona zawiera podstawowe elementy
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertContains(response, '<form')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_settings_validation_feedback(self):
        """Test informacji zwrotnej przy walidacji ustawień"""
        response = self.client.post(reverse('profile'), {
            'email_frequency': 'invalid'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
#python manage.py test articles.tests.test_settings_ui --settings=ai_news.test_settings
