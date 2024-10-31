# articles/scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .models import Article, Category
from transformers import pipeline


summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def generate_summary(text, max_length=130, min_length=30):
    """
    Funkcja do generowania streszczenia przy użyciu modelu BART.
    """
    # Używamy modelu, by stworzyć streszczenie
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

def fetch_article_content(url):
    """
    Pobiera pełną treść artykułu z danego URL.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Błąd pobierania artykułu z URL: {url}")
        return "Treść niedostępna"

    soup = BeautifulSoup(response.text, 'html.parser')

    # Znalezienie głównej treści artykułu - zwykle w divie lub sekcji o specyficznej klasie
    content_div = soup.find('div', class_='article-content')  # Klasa może się różnić w zależności od struktury strony

    if not content_div:
        return "Treść niedostępna"

    # Wyciąganie tekstu z paragrafów
    paragraphs = content_div.find_all('p')
    content = " ".join([p.get_text() for p in paragraphs])

    return content


def scrape_ai_articles():
    url = "https://techcrunch.com/tag/ai/"  # URL TechCrunch z artykułami o AI
    response = requests.get(url)

    # Upewniamy się, że strona odpowiada poprawnie
    if response.status_code != 200:
        print("Błąd pobierania strony:", response.status_code)
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Znajdujemy kategorię 'AI' lub ją tworzymy
    category, _ = Category.objects.get_or_create(name="AI")

    # Znajdujemy artykuły
    articles = soup.find_all('li', class_='wp-block-post', limit=5)  # Znajdujemy 5 najnowszych artykułów
    for article in articles:
        # Pobieramy tytuł i link
        title_tag = article.find('h3', class_='loop-card__title')
        title = title_tag.get_text(strip=True) if title_tag else "Brak tytułu"
        link_tag = title_tag.find('a') if title_tag else None
        url = link_tag['href'] if link_tag else "#"

        # Pobieramy autora
        author_tag = article.find('a', class_='loop-card__author')
        author = author_tag.get_text(strip=True) if author_tag else "Nieznany autor"

        # Pobieramy datę publikacji
        date_tag = article.find('time', class_='loop-card__time')
        pub_date = datetime.strptime(date_tag['datetime'], '%Y-%m-%dT%H:%M:%S%z') if date_tag else datetime.now()

        article_content = fetch_article_content(url)

        # Generujemy streszczenie
        summary = extract_intro(article_content)

        # Dodanie artykułu do bazy danych
        Article.objects.get_or_create(
            title=title,
            url=url,
            summary=summary,
            # author=author,
            category=category,
            publication_date=pub_date
        )

    print("Scrapowanie zakończone. Dodano artykuły z TechCrunch.")
