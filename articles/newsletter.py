from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from articles.models import UserProfile, Article

#
# def send_article_emails():
#     """
#     Funkcja wysyła e-maile do użytkowników z 5 najnowszymi artykułami
#     z wybranych przez nich kategorii.
#     """
#     user_profiles = UserProfile.objects.prefetch_related('selected_categories').all()
#
#     for profile in user_profiles:
#         selected_categories = profile.selected_categories.all()
#
#         # Pobierz 5 najnowszych artykułów według daty publikacji
#         articles = Article.objects.filter(
#             category__in=selected_categories
#         ).order_by('-publication_date')[:5]
#
#         if articles.exists():
#             subject = "Nowe artykuły z Twoich ulubionych kategorii"
#             message = "Cześć,\n\nOto najnowsze artykuły, które mogą Cię zainteresować:\n\n"
#             for article in articles:
#                 message += f"- {article.title}\n  Link: {article.url}\n  Opis: {article.summary}\n\n"
#             message += "Pozdrawiamy,\nZespół Twojej aplikacji"
#
#             # Wysłanie e-maila
#             send_mail(
#                 subject,
#                 message,
#                 'noreply@newslettertechnologiczny.com',  # Adres nadawcy
#                 [profile.user.email],  # Adres odbiorcy
#                 fail_silently=False,
#             )
#             print(f"E-mail wysłany do {profile.user.email}")

# articles/newsletter.py

# articles/newsletter.py

# articles/newsletter.py

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from articles.models import UserProfile, Article

def format_plain_text_email(articles, username):
    """Helper function to format plain text version of the email"""
    message = f"Cześć {username}!\n\nOto najnowsze artykuły, które mogą Cię zainteresować:\n\n"
    for article in articles:
        message += (f"- {article.title}\n"
                   f"  Opis: {article.summary}\n"
                   f"  Czytaj więcej: {article.url}\n\n")
    message += "Pozdrawiamy,\nZespół Newsletter Technologiczny"
    return message

def send_article_emails():
    """
    Funkcja wysyła e-maile do użytkowników z 5 najnowszymi artykułami
    z wybranych przez nich kategorii.
    """
    user_profiles = UserProfile.objects.prefetch_related('selected_categories').all()

    for profile in user_profiles:
        selected_categories = profile.selected_categories.all()
        articles = Article.objects.filter(
            category__in=selected_categories
        ).order_by('-publication_date')[:5]

        if articles.exists():
            subject = "Nowe artykuły z Twoich ulubionych kategorii"
            from_email = 'noreply@newslettertechnologiczny.com'
            text_content = format_plain_text_email(articles, profile.user.username)
            recipient_list = [profile.user.email]

            try:
                html_content = render_to_string('article_email.html', {
                    'user': profile.user,
                    'articles': articles
                })

                if not html_content:
                    raise ValueError("Empty HTML content")

                # Próba wysłania wersji HTML
                msg = EmailMultiAlternatives(
                    subject,
                    text_content,
                    from_email,
                    recipient_list
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                print(f"E-mail HTML wysłany do {profile.user.email}")

            except Exception as e:
                print(f"Błąd podczas wysyłania HTML email: {str(e)}")
                # Wysyłanie prostej wersji tekstowej
                plain_msg = EmailMessage(
                    subject,
                    text_content,
                    from_email,
                    recipient_list
                )
                plain_msg.send()
                print(f"E-mail tekstowy wysłany do {profile.user.email}")
