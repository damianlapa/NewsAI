from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils.timezone import now
from django.db import transaction
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import re

from articles.models import Article, Category, UserProfile
from articles.newsletter import send_article_emails
from articles.scraper import (
    scrape_articles,
    fetch_article_content,
    generate_summary,
    parse_date,
)

class ScraperTest(TestCase):
    """Testy dla scrapera - nie potrzebują użytkowników ani profili"""
    def test_scrape_articles(self):
        mock_html = '''
        <html>
            <li class="wp-block-post">
                <h3 class="loop-card__title">
                    <a href="/test-article">Test Article</a>
                </h3>
                <time class="loop-card__time" datetime="2024-03-20T10:00:00+00:00">
                    March 20, 2024
                </time>
            </li>
        </html>
        '''
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = mock_html
            articles = scrape_articles('techcrunch', 'AI')
            self.assertTrue(len(articles) > 0)
            self.assertEqual(articles[0]['title'], 'Test Article')

    def test_fetch_article_content(self):
        mock_html = '''
        <div class="article-content">
            <p>Test paragraph 1</p>
            <p>Test paragraph 2</p>
        </div>
        '''
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = mock_html
            content = fetch_article_content('https://example.com/article')
            self.assertIsNotNone(content)
            self.assertIn('Test paragraph 1', content)

    def test_parse_date(self):
        test_cases = [
            ('2024-03-20T10:00:00+0000', '%Y-%m-%dT%H:%M:%S%z'),
            ('March 20, 2024', '%B %d, %Y'),
            ('03/20/2024', '%m/%d/%Y')
        ]
        for date_str, date_format in test_cases:
            parsed_date = parse_date(date_str, date_format)
            self.assertIsInstance(parsed_date, datetime)


class NewsletterTest(TestCase):
    def setUp(self):
        with transaction.atomic():
            # Tworzenie podstawowych danych testowych
            self.category = Category.objects.create(
                name='Sztuczna Inteligencja i Uczenie Maszynowe'
            )

            # Tworzenie użytkownika z unikalnym ID
            self.user = User.objects.create_user(
                username=f'testuser_newsletter_{User.objects.count()}',
                email=f'testuser_newsletter_{User.objects.count()}@example.com',
                password='testpass123'
            )
            self.profile, created = UserProfile.objects.get_or_create(user=self.user)
            self.profile.selected_categories.add(self.category)

            # Tworzenie artykułów testowych
            for i in range(6):
                Article.objects.create(
                    title=f'Test Article {i}',
                    url=f'https://example.com/article{i}',
                    summary=f'Summary {i}',
                    category=self.category,
                    publication_date=now() - timedelta(days=i)
                )

    def test_newsletter_content_personalization(self):
        send_article_emails()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        for i in range(5):
            self.assertIn(f'Test Article {i}', email.body)


class IntegrationTest(TestCase):
    def setUp(self):
        with transaction.atomic():
            # Tworzenie podstawowych danych testowych
            self.category = Category.objects.create(
                name='Sztuczna Inteligencja i Uczenie Maszynowe'
            )

            # Tworzenie użytkownika z unikalnym ID
            self.user = User.objects.create_user(
                username=f'testuser_integration_{User.objects.count()}',
                email=f'testuser_integration_{User.objects.count()}@example.com',
                password='testpass123'
            )
            self.profile, created = UserProfile.objects.get_or_create(user=self.user)

    def test_full_scraping_workflow(self):
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = '''
                <li class="wp-block-post">
                    <h3 class="loop-card__title">
                        <a href="/test-article">Latest AI Development</a>
                    </h3>
                    <time class="loop-card__time" datetime="2024-03-20T10:00:00+0000">
                        March 20, 2024
                    </time>
                </li>
            '''
            self.profile.selected_categories.add(self.category)
            articles = scrape_articles('techcrunch', 'AI')

            # Ręcznie tworzymy artykuł na podstawie scraped data
            if articles:
                article_data = articles[0]
                Article.objects.create(
                    title=article_data['title'],
                    url=article_data['url'],
                    summary="Test summary",
                    category=self.category,
                    publication_date=article_data['publication_date']
                )

            # Sprawdzamy czy artykuł został utworzony
            self.assertTrue(Article.objects.filter(category=self.category).exists())

            # Dodatkowe asercje
            article = Article.objects.first()
            self.assertEqual(article.title, 'Latest AI Development')
            self.assertTrue(article.url.endswith('/test-article'))


class ContentPersonalizationTest(TestCase):
    def setUp(self):
        with transaction.atomic():
            # Tworzenie kategorii
            self.ai_category = Category.objects.create(name='Sztuczna Inteligencja')
            self.iot_category = Category.objects.create(name='Internet Rzeczy')
            self.cloud_category = Category.objects.create(name='Chmura')

            # Tworzenie użytkowników z różnymi preferencjami
            self.user1 = User.objects.create_user(
                username='ai_enthusiast',
                email='ai@test.com',
                password='test123'
            )
            self.profile1, _ = UserProfile.objects.get_or_create(user=self.user1)
            self.profile1.selected_categories.add(self.ai_category)

            self.user2 = User.objects.create_user(
                username='iot_enthusiast',
                email='iot@test.com',
                password='test123'
            )
            self.profile2, _ = UserProfile.objects.get_or_create(user=self.user2)
            self.profile2.selected_categories.add(self.iot_category)

            # Tworzenie artykułów z różnych kategorii
            self.ai_articles = [
                Article.objects.create(
                    title=f'AI Article {i}',
                    url=f'https://example.com/ai{i}',
                    summary=f'AI Summary {i}',
                    category=self.ai_category,
                    publication_date=now() - timedelta(days=i)
                ) for i in range(3)
            ]

            self.iot_articles = [
                Article.objects.create(
                    title=f'IoT Article {i}',
                    url=f'https://example.com/iot{i}',
                    summary=f'IoT Summary {i}',
                    category=self.iot_category,
                    publication_date=now() - timedelta(days=i)
                ) for i in range(3)
            ]

    def test_content_personalization(self):
        """Test czy użytkownicy otrzymują artykuły tylko z wybranych kategorii"""
        send_article_emails()

        # Sprawdź email dla użytkownika zainteresowanego AI
        ai_email = next(email for email in mail.outbox if email.to[0] == 'ai@test.com')
        for article in self.ai_articles:
            self.assertIn(article.title, ai_email.body)
        for article in self.iot_articles:
            self.assertNotIn(article.title, ai_email.body)

        # Sprawdź email dla użytkownika zainteresowanego IoT
        iot_email = next(email for email in mail.outbox if email.to[0] == 'iot@test.com')
        for article in self.iot_articles:
            self.assertIn(article.title, iot_email.body)
        for article in self.ai_articles:
            self.assertNotIn(article.title, iot_email.body)


class AIContentGenerationTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.test_text = """
        Deep learning has revolutionized artificial intelligence, enabling breakthroughs 
        in natural language processing and computer vision. Recent advances in transformer 
        models have led to significant improvements in various AI applications.
        """

    def test_summary_quality(self):
        """Test jakości generowanych streszczeń"""
        summary = generate_summary(self.test_text)

        # Sprawdź czy podsumowanie nie jest puste
        self.assertTrue(len(summary) > 0)

        # Sprawdź czy podsumowanie ma rozsądną długość
        self.assertTrue(10 <= len(summary.split()) <= 50)

        # Sprawdź czy podsumowanie zawiera kluczowe słowa
        key_terms = ['deep learning', 'artificial intelligence', 'transformer']
        self.assertTrue(any(term.lower() in summary.lower() for term in key_terms))

        # Sprawdź czy podsumowanie kończy się poprawnie
        self.assertTrue(summary.endswith('.'))

    def test_summary_error_handling(self):
        """Test obsługi błędów podczas generowania streszczeń"""
        # Test dla pustego tekstu
        empty_summary = generate_summary("")
        self.assertEqual(empty_summary, "No content available for summarization.")

        # Test dla bardzo krótkiego tekstu
        short_text = "Hello world."
        short_summary = generate_summary(short_text)
        self.assertTrue(len(short_summary) > 0)

class MultiSourceScrapingTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='AI')

    @patch('articles.scraper.requests.get')
    def test_multiple_source_scraping(self, mock_get):
        """Test scrapowania z wielu źródeł"""
        # Przygotuj różne odpowiedzi dla różnych źródeł
        mock_responses = {
            'techcrunch': '''
                <li class="wp-block-post">
                    <h3 class="loop-card__title">
                        <a href="/tc-article">TechCrunch Article</a>
                    </h3>
                    <time class="loop-card__time">2024-03-20T10:00:00+0000</time>
                </li>
            ''',
            'theverge': '''
                <article>
                    <h2><a href="/verge-article">Verge Article</a></h2>
                    <time>2024-03-20T10:00:00.000Z</time>
                </article>
            '''
        }

        def mock_get_response(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            url = args[0]
            if 'techcrunch' in url:
                mock_response.text = mock_responses['techcrunch']
            elif 'theverge' in url:
                mock_response.text = mock_responses['theverge']
            return mock_response

        mock_get.side_effect = mock_get_response

        # Test scrape_all_articles
        for source in ['techcrunch', 'theverge']:
            articles = scrape_articles(source, 'AI')
            self.assertTrue(len(articles) > 0)
            if source == 'techcrunch':
                self.assertIn('TechCrunch Article', articles[0]['title'])
            elif source == 'theverge':
                self.assertIn('Verge Article', articles[0]['title'])


class NewsletterFormattingTest(TestCase):
    def setUp(self):
        # Wyczyść dane
        Category.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Article.objects.all().delete()

        self.category = Category.objects.create(name='Test Category')
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123'
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.selected_categories.add(self.category)

        # Tworzenie testowego artykułu
        self.article = Article.objects.create(
            title='Test Article',
            url='https://example.com/test',
            summary='Test Summary',
            category=self.category,
            publication_date=now()
        )

    def test_newsletter_formatting(self):
        """Test formatowania newslettera dla wersji HTML i tekstowej"""
        # Wyczyść skrzynkę przed testem
        mail.outbox = []

        send_article_emails()

        # Sprawdź czy email został wysłany
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        # Test plain text version
        self.assertIn('Test Article', email.body)
        self.assertIn('Test Summary', email.body)
        self.assertIn('Czytaj więcej', email.body)

        # Test if email has alternative content
        self.assertTrue(len(email.alternatives) > 0)

        # Check HTML content
        html_content = next(alt[0] for alt in email.alternatives if 'text/html' in alt[1])

        # Check HTML structure
        self.assertTrue(re.search(r'<html.*?>', html_content))
        self.assertTrue(re.search(r'<body.*?>', html_content))
        self.assertTrue('<div class="container"' in html_content)
        self.assertTrue('<div class="article"' in html_content)

        # Check responsive styles
        self.assertTrue('@media' in html_content)
        self.assertTrue('max-width' in html_content)

        # Check content
        self.assertIn(self.article.title, html_content)
        self.assertIn(self.article.summary, html_content)
        self.assertIn(self.article.url, html_content)

        # Check link formatting
        self.assertIn(f'href="{self.article.url}"', html_content)

        # Verify personalization
        self.assertIn(self.user.username, html_content)

        # Verify metadata
        self.assertEqual(email.subject, "Nowe artykuły z Twoich ulubionych kategorii")
        self.assertEqual(email.from_email, 'noreply@newslettertechnologiczny.com')
        self.assertEqual(email.to, [self.user.email])

    def test_email_content_formatting(self):
        """Test poprawnego formatowania treści emaila"""
        mail.outbox = []
        send_article_emails()

        email = mail.outbox[0]

        # Sprawdź format tekstowy
        expected_text = (
            f"Cześć {self.user.username}!\n\n"
            "Oto najnowsze artykuły, które mogą Cię zainteresować:\n\n"
            f"- {self.article.title}\n"
            f"  Opis: {self.article.summary}\n"
            f"  Czytaj więcej: {self.article.url}\n\n"
            "Pozdrawiamy,\nZespół Newsletter Technologiczny"
        )
        self.assertIn(expected_text.strip(), email.body.strip())

    def tearDown(self):
        # Wyczyść dane po teście
        Category.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Article.objects.all().delete()
