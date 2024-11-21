# articles/scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .models import Article, Category
from transformers import pipeline
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Define logger

# Initialize the summarizer pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

from transformers import BartTokenizer

# Initialize the tokenizer
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")


@dataclass
class ScrapingConfig:
    """Configuration for each source website"""
    base_url: str
    category_urls: Dict[str, str]
    article_selector: str
    title_selector: str
    link_selector: str
    author_selector: str
    date_selector: str
    date_format: str


SOURCES_CONFIG = {
    'techcrunch': ScrapingConfig(
        base_url='https://techcrunch.com',
        category_urls={
            'AI': '/tag/artificial-intelligence/',
            'IoT': '/tag/internet-of-things/',
            'CS': '/tag/security/',
            'RA': '/tag/robotics/',
            'TC': '/tag/cloud/',
            'TM': '/tag/mobile/'
        },
        article_selector='li.wp-block-post',
        title_selector='h3.loop-card__title',
        link_selector='h3.loop-card__title a',
        author_selector='a.loop-card__author',
        date_selector='time.loop-card__time',
        date_format='%Y-%m-%dT%H:%M:%S%z'
    ),
    'theverge': ScrapingConfig(
        base_url='https://www.theverge.com',
        category_urls={
            'AI': '/ai-artificial-intelligence',
            'CS': '/cyber-security',
            'TM': '/mobile'
            # Usunięto TC (cloud-computing) - niedziałający URL
        },
        article_selector='article',
        title_selector='h2',
        link_selector='h2 a',
        author_selector='.text-gray-63',
        date_selector='time',
        date_format='%Y-%m-%dT%H:%M:%S.%fZ'
    ),
    'wired': ScrapingConfig(
        base_url='https://www.wired.com',
        category_urls={
            'AI': '/tag/artificial-intelligence',
            'IoT': '/tag/internet-of-things',
            'CS': '/tag/security',
            'TK': '/tag/quantum-computing'
            # Usunięto BT i NT - niedziałające URL-e
        },
        article_selector='article.archive-item-component',
        title_selector='h2.archive-item-component__title',
        link_selector='a.archive-item-component__link',
        author_selector='.byline__name',
        date_selector='time',
        date_format='%Y-%m-%d'
    ),
    'sciencenews': ScrapingConfig(
        base_url='https://www.sciencenews.org',
        category_urls={
            'AI': '/topic/artificial-intelligence',
            'TK': '/topic/quantum-physics'
            # Usunięto BT, NT, EO - niedziałające URL-e
        },
        article_selector='article.post-item',
        title_selector='h3.post-item-river__title',
        link_selector='h3.post-item-river__title a',
        author_selector='.post-item-river__author',
        date_selector='.post-item-river__date',
        date_format='%B %d, %Y'
    ),
    'zdnet': ScrapingConfig(
        base_url='https://www.zdnet.com',
        category_urls={
            'AI': '/topic/artificial-intelligence',
            'IoT': '/topic/internet-of-things',
            'CS': '/topic/security',
            'TC': '/topic/cloud',
            'TM': '/topic/mobility'
        },
        article_selector='article.item',
        title_selector='h3.title',
        link_selector='h3.title a',
        author_selector='.author',
        date_selector='time',
        date_format='%Y-%m-%dT%H:%M:%S%z'
    ),
    'nanowerk': ScrapingConfig(
        base_url='https://www.nanowerk.com',
        category_urls={
            'NT': '/category-nanoresearch.php',
            'BT': '/category-biotech.php',
            'EO': '/category-cleantech.php',
            'RA': '/category-robotics.php'
        },
        article_selector='article.post',
        title_selector='h2.entry-title',
        link_selector='h2.entry-title a',
        author_selector='.author',
        date_selector='.published',
        date_format='%B %d, %Y'
    ),
    'renewable_energy': ScrapingConfig(
        base_url='https://www.renewableenergyworld.com',
        category_urls={
            'EO': '/wind-power/',
            'NT': '/energy-storage/'
        },
        article_selector='div.article-preview',
        title_selector='h3.article-title',
        link_selector='h3.article-title a',
        author_selector='.article-author',
        date_selector='.article-date',
        date_format='%m/%d/%Y'
    )
}


def verify_urls():
    for source, config in SOURCES_CONFIG.items():
        for category, url in config.category_urls.items():
            try:
                full_url = urljoin(config.base_url, url)
                response = requests.head(full_url)
                if response.status_code == 404:
                    logger.warning(f"Invalid URL for {source} - {category}: {full_url}")
            except Exception as e:
                logger.error(f"Error checking {source} - {category}: {e}")


def generate_summary(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """Generates a summary of the provided text using the BART model"""
    if not text:
        return "No content available for summarization."

    inputs = tokenizer(text, truncation=True, max_length=1024, return_attention_mask=False, return_token_type_ids=False)
    truncated_text = tokenizer.decode(inputs['input_ids'], skip_special_tokens=True)

    try:
        summary = summarizer(truncated_text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Summary could not be generated due to an error."


def fetch_article_content(url: str) -> Optional[str]:
    """Fetches the main content of an article from a given URL"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        abstract = soup.find('div', class_='c-article-section__content')
        if abstract:
            return abstract.get_text(strip=True)
    except requests.RequestException as e:
        logger.error(f"Error fetching article content from URL {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Define content selectors
    content_selectors = [
        {'tag': 'div', 'class': ['entry-content', 'wp-block-post-content']},
        {'tag': 'div', 'class': ['article-content', 'post-content']},
        {'tag': 'div', 'class': ['main-content', 'content-body']},
        {'tag': 'article', 'class': ['article-body', 'post-content']},
        {'tag': 'main', 'class': ['main-content', 'article-main']},
        {'tag': 'section', 'class': ['content', 'article-content']}
    ]

    # Try each selector
    for selector in content_selectors:
        for class_name in selector['class']:
            content_div = soup.find(selector['tag'], class_=class_name)
            if content_div:
                paragraphs = content_div.find_all('p')
                content = " ".join([p.get_text() for p in paragraphs])
                if content.strip():
                    return content

    # Fallback to main or article tags
    main_content = soup.find('main') or soup.find('article')
    if main_content:
        paragraphs = main_content.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])
        if content.strip():
            return content

    return None

def parse_date(date_str: str, date_format: str) -> datetime:
    """Parses date string to datetime object with error handling"""
    try:
        return datetime.strptime(date_str, date_format)
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return datetime.now()


def scrape_articles(source: str, category_code: str) -> List[Dict]:
    """Scrapes articles from a specific source and category"""
    # verify_urls()
    config = SOURCES_CONFIG[source]
    category_url = urljoin(config.base_url, config.category_urls[category_code])

    try:
        response = requests.get(category_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching {source} - {category_code}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles_data = []

    for article in soup.select(config.article_selector)[:5]:  # Limit to 5 articles
        try:
            title_elem = article.select_one(config.title_selector)
            link_elem = article.select_one(config.link_selector)
            date_elem = article.select_one(config.date_selector)

            if not all([title_elem, link_elem]):
                continue

            title = title_elem.get_text(strip=True)
            url = link_elem.get('href')
            if not url.startswith('http'):
                url = urljoin(config.base_url, url)

            pub_date = parse_date(
                date_elem.get('datetime', date_elem.get_text(strip=True)),
                config.date_format
            ) if date_elem else datetime.now()

            articles_data.append({
                'title': title,
                'url': url,
                'publication_date': pub_date
            })

        except Exception as e:
            logger.error(f"Error processing article from {source}: {e}")
            continue

    return articles_data


def scrape_all_articles():
    """Scrapes articles from all sources for all configured categories"""
    verify_urls()
    for category_code, category_name in {
        'AI': 'Sztuczna Inteligencja i Uczenie Maszynowe',
        'IoT': 'Internet Rzeczy',
        'CS': 'Cyberbezpieczeństwo',
        'RA': 'Robotyka i Automatyzacja',
        'TC': 'Technologie Chmurowe',
        'TM': 'Technologie Mobilne',
        'BT': 'Biotechnologia',
        'NT': 'Nanotechnologia',
        'EO': 'Energetyka Odnawialna',
        'TK': 'Technologie Kwantowe'
    }.items():
        category, _ = Category.objects.get_or_create(name=category_name)

        for source, config in SOURCES_CONFIG.items():
            if category_code in config.category_urls:
                articles = scrape_articles(source, category_code)

                for article_data in articles:
                    try:
                        # Check if article already exists
                        if not Article.objects.filter(url=article_data['url']).exists():
                            content = fetch_article_content(article_data['url'])
                            if content:
                                summary = generate_summary(content)

                                Article.objects.create(
                                    title=article_data['title'],
                                    url=article_data['url'],
                                    summary=summary,
                                    category=category,
                                    publication_date=article_data['publication_date']
                                )
                                logger.info(f"Added article: {article_data['title']}")

                    except Exception as e:
                        logger.error(f"Error saving article {article_data['title']}: {e}")
                        continue

        logger.info(f"Completed scraping for category: {category_name}")
