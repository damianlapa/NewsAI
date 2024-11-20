from celery import shared_task
from articles.models import UserProfile
from memory_profiler import profile
from ai_news import settings
from articles.newsletter import send_article_emails
from articles.scraper import scrape_all_articles
import logging
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

@shared_task
@profile
def scrape_articles_task():
    logger.info("Starting scrape_articles_task")
    try:
        scrape_all_articles()
    except Exception as e:
        logger.error(f"Error in scrape_articles_task: {e}")
        raise

@shared_task
def send_newsletter():
    logger.info("Starting send_newsletter task")
    try:
        send_article_emails()
        logger.info("Newsletter sent successfully")
    except Exception as e:
        logger.error(f"Error in send_newsletter task: {e}")
        raise

