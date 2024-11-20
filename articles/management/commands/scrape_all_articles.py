from django.core.management.base import BaseCommand
from articles.scraper import scrape_all_articles

class Command(BaseCommand):
    help = "Scrapes articles from multiple sources and categories and saves them to the database"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting article scraping...")
        scrape_all_articles()
        self.stdout.write(self.style.SUCCESS("Article scraping completed successfully"))
