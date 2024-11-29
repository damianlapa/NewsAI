from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from articles.models import Category, Article, UserProfile


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    LOGIN_URL='/login/',
    LOGIN_REDIRECT_URL='/'
)
class UITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Konfiguracja danych testowych na poziomie klasy"""
        # Tworzenie kategorii
        cls.category = Category.objects.create(name='AI')

    def setUp(self):
        """Konfiguracja przed każdym testem"""
        # Wyczyść dane użytkowników i profili
        User.objects.all().delete()
        UserProfile.objects.all().delete()
        Article.objects.all().delete()

        # Tworzenie testowego użytkownika
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Użyj get_or_create dla profilu
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.selected_categories.add(self.category)

        # Tworzenie artykułu
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com',
            summary='Test summary',
            category=self.category,
            publication_date='2024-01-01'
        )

        # Utwórz klienta i zaloguj użytkownika
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_homepage_layout(self):
        """Test wyglądu strony głównej"""
        response = self.client.get(reverse('home'))

        # Sprawdź status i szablony - powinien używać base.html i articles/main.html
        self.assertEqual(response.status_code, 200)

        templates_used = [t.name for t in response.templates]
        self.assertIn('base.html', templates_used)
        self.assertIn('articles/main.html', templates_used)

        # Sprawdź elementy nawigacji
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Articles')
        self.assertContains(response, 'Profile')

    def test_articles_page_layout(self):
        """Test wyglądu strony z artykułami"""
        response = self.client.get(reverse('user-articles'))

        # Sprawdź status i podstawowe elementy
        self.assertEqual(response.status_code, 200)
        self.assertIn('base.html', [t.name for t in response.templates])

        # Sprawdź elementy artykułu
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.summary)
        self.assertContains(response, 'Czytaj więcej')

    def test_responsive_design(self):
        """Test responsywności strony"""
        response = self.client.get(reverse('home'))

        # Sprawdź meta viewport tag
        self.assertContains(response, 'viewport')
        self.assertContains(response, 'width=device-width')

        # Sprawdź obecność klas Bootstrap
        self.assertContains(response, 'container')

    def test_user_feedback(self):
        """Test informacji zwrotnej dla użytkownika"""
        # Usuń wszystkie artykuły
        Article.objects.all().delete()

        # Sprawdź komunikat o braku artykułów
        response = self.client.get(reverse('user-articles'))
        self.assertContains(response, 'Brak artykułów')

    def test_authentication_required(self):
        """Test wymagania logowania"""
        # Wyloguj użytkownika
        self.client.logout()

        # Spróbuj dostać się do chronionej strony
        protected_url = reverse('user-articles')
        response = self.client.get(protected_url)

        # Sprawdź przekierowanie do logowania
        self.assertEqual(response.status_code, 302)
        login_url = f"{settings.LOGIN_URL}?next={protected_url}"
        self.assertEqual(response.url, login_url)

    def test_user_profile(self):
        """Test strony profilu użytkownika"""
        response = self.client.get(reverse('profile'))

        # Sprawdź status i szablon
        self.assertEqual(response.status_code, 200)
        self.assertIn('users/profile.html', [t.name for t in response.templates])

        # Sprawdź czy kategorie są wyświetlane
        self.assertContains(response, self.category.name)

    def tearDown(self):
        """Czyszczenie po każdym teście"""
        User.objects.all().delete()
        UserProfile.objects.all().delete()
        Article.objects.all().delete()

#python manage.py test articles.tests.test_ui --settings=ai_news.test_settings
