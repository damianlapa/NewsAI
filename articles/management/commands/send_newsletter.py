from django.core.management.base import BaseCommand
from articles.newsletter import send_article_emails


class Command(BaseCommand):
    help = "Wysyła newsletter"

    def handle(self, *args, **kwargs):
        send_article_emails()
        self.stdout.write(self.style.SUCCESS("Wysłano wiadomości"))
