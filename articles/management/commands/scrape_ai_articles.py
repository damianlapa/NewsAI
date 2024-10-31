from django.core.management.base import BaseCommand
from articles.scraper import scrape_ai_articles


class Command(BaseCommand):
    help = "Scrapuje artykuły o AI i zapisuje je w bazie danych"

    def handle(self, *args, **kwargs):
        scrape_ai_articles()
        self.stdout.write(self.style.SUCCESS("Scrapowanie zakończone pomyślnie"))
