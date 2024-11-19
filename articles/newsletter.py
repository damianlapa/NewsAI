from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from articles.models import UserProfile, Article


def send_article_emails():
    """
    Funkcja wysyła e-maile do użytkowników z 5 najnowszymi artykułami
    z wybranych przez nich kategorii.
    """
    user_profiles = UserProfile.objects.prefetch_related('selected_categories').all()

    for profile in user_profiles:
        selected_categories = profile.selected_categories.all()

        # Pobierz 5 najnowszych artykułów według daty publikacji
        articles = Article.objects.filter(
            category__in=selected_categories
        ).order_by('-publication_date')[:5]

        if articles.exists():
            subject = "Nowe artykuły z Twoich ulubionych kategorii"
            message = "Cześć,\n\nOto najnowsze artykuły, które mogą Cię zainteresować:\n\n"
            for article in articles:
                message += f"- {article.title}\n  Link: {article.url}\n  Opis: {article.summary}\n\n"
            message += "Pozdrawiamy,\nZespół Twojej aplikacji"

            # Wysłanie e-maila
            send_mail(
                subject,
                message,
                'noreply@newslettertechnologiczny.com',  # Adres nadawcy
                [profile.user.email],  # Adres odbiorcy
                fail_silently=False,
            )
            print(f"E-mail wysłany do {profile.user.email}")
