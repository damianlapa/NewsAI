# articles/scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .models import Article, Category
from transformers import pipeline
import logging  # Import logging module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Define logger

# Initialize the summarizer pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


from transformers import BartTokenizer

# Initialize the tokenizer
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

from transformers import BartTokenizer

# Initialize the tokenizer
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

def generate_summary(text, max_length=130, min_length=30):
    """
    Generates a summary of the provided text using the BART model,
    compatible with TensorFlow environments.
    """
    if not text:
        return "No content available for summarization."

    # Tokenize the text with truncation, using plain strings
    inputs = tokenizer(text, truncation=True, max_length=1024, return_attention_mask=False, return_token_type_ids=False)

    # Decode the truncated input back to text
    truncated_text = tokenizer.decode(inputs['input_ids'], skip_special_tokens=True)

    try:
        summary = summarizer(truncated_text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Summary could not be generated due to an error."



def fetch_article_content(url):
    """
    Fetches the main content of an article from a given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching article content from URL {url}: {e}")
        return None  # Return None to handle downstream

    soup = BeautifulSoup(response.text, 'html.parser')

    # Attempt to find the main content in various containers
    possible_containers = [
        {'tag': 'div', 'class': 'entry-content wp-block-post-content'},
        {'tag': 'div', 'class': 'article-content'},
        {'tag': 'div', 'class': 'main-content'},
        {'tag': 'article'},
        {'tag': 'section', 'class': 'content'},
        {'tag': 'main', 'class': 'wp-block-group template-content'},
    ]

    content = None
    for container in possible_containers:
        content_div = soup.find(container['tag'], class_=container.get('class'))
        if content_div:
            # Extract paragraphs within this container
            paragraphs = content_div.find_all('p')
            content = " ".join([p.get_text() for p in paragraphs])
            if content.strip():  # If content was found, break out of the loop
                logger.info(f"Content found in container {container['tag']} with class {container.get('class')}")
                break
            else:
                logger.warning(f"Empty content in container {container['tag']} with class {container.get('class')}")

    # Fallback: If no container was found, attempt to retrieve all text from <p> tags in <main>
    if not content:
        main_content = soup.find('main')
        if main_content:
            paragraphs = main_content.find_all('p')
            content = " ".join([p.get_text() for p in paragraphs])
            logger.info("Fallback to <main> tag for content extraction.")

    # Final check: Ensure the content is not empty
    if not content or not content.strip():
        logger.warning(f"Content not found or empty for URL: {url}")
        return "Treść niedostępna"

    return content


def scrape_ai_articles():
    url = "https://techcrunch.com/tag/ai/"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching the page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    category, _ = Category.objects.get_or_create(name="AI")
    articles = soup.find_all('li', class_='wp-block-post', limit=5)

    for article in articles:
        title_tag = article.find('h3', class_='loop-card__title')
        title = title_tag.get_text(strip=True) if title_tag else "Brak tytułu"
        link_tag = title_tag.find('a') if title_tag else None
        url = link_tag['href'] if link_tag else "#"

        author_tag = article.find('a', class_='loop-card__author')
        author = author_tag.get_text(strip=True) if author_tag else "Nieznany autor"

        date_tag = article.find('time', class_='loop-card__time')
        pub_date = datetime.strptime(date_tag['datetime'], '%Y-%m-%dT%H:%M:%S%z') if date_tag else datetime.now()

        # Fetch and summarize article content
        article_content = fetch_article_content(url)
        summary = generate_summary(article_content)

        # Add article to the database, checking for duplicates based on title and publication date
        Article.objects.get_or_create(
            title=title,
            url=url,
            summary=summary,
            # author=author,
            category=category,
            publication_date=pub_date
        )

    logger.info("Scraping completed. AI articles from TechCrunch have been added.")
