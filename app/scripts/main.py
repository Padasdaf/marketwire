from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from datetime import datetime
from typing import List, Dict

app = Flask(__name__)
CORS(app)

# Initialize the sentiment analysis pipeline
analyzer = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert"
)

def scrape_yahoo_finance_news_with_titles(company_symbol: str):
    """
    Scrape news article titles and URLs from Yahoo Finance for a specific company.
    """
    articles = []
    url = f"https://finance.yahoo.com/quote/{company_symbol}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.find_all('div', class_='content yf-fy4jvv')

        for item in news_items:
            link = item.find('a', class_='subtle-link')
            if link and link.get('href'):
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://finance.yahoo.com{article_url}"

                title = link.find('h3').get_text(strip=True) if link.find('h3') else "No title available"
                articles.append({'title': title, 'url': article_url})

    return articles

def analyze_sentiment(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Analyze the sentiment of the articles and add sentiment analysis to each.
    """
    analyzed_articles = []
    for article in articles:
        text = article['title']  # You can also include content if available
        result = analyzer(text)[0]
        label = result['label'].lower()
        score = result['score']

        # Map sentiment labels to colors
        sentiment_color = 'green' if label == 'positive' else 'red' if label == 'negative' else 'gray'

        article['sentiment_label'] = label
        article['sentiment_score'] = score
        article['sentiment_color'] = sentiment_color  # Add color for sentiment
        analyzed_articles.append(article)

    return analyzed_articles

@app.route('/api/news', methods=['GET'])
def get_news():
    company_symbol = request.args.get('symbol', default='AMZN', type=str)
    articles = scrape_yahoo_finance_news_with_titles(company_symbol)
    analyzed_articles = analyze_sentiment(articles)  # Analyze sentiment
    return jsonify(analyzed_articles)

if __name__ == '__main__':
    app.run(debug=True)