from transformers import pipeline
from datetime import datetime
from typing import List, Dict

class SentimentAnalyzer:
    def __init__(self):
        # Initialize the sentiment analysis pipeline
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",  # Financial domain-specific BERT model
            tokenizer="ProsusAI/finbert"
        )

    def analyze_text(self, text: str) -> tuple:
        """
        Analyze the sentiment of a given text.
        Returns: (sentiment_label, sentiment_score)
        """
        try:
            max_length = 512  # BERT models typically have a max length of 512 tokens
            if len(text.split()) > max_length:
                text = " ".join(text.split()[:max_length])

            result = self.analyzer(text)[0]
            label = result['label'].lower()  # Convert to lowercase for consistency
            score = result['score']

            # Map sentiment labels and normalize scores
            sentiment_map = {
                'positive': 1.0,
                'negative': -1.0,
                'neutral': 0.0
            }
            normalized_score = sentiment_map.get(label, 0.0) * score
            return label, normalized_score

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return "neutral", 0.0

    def analyze_articles(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Analyze a list of articles and add sentiment analysis to each.
        """
        analyzed_articles = []
        for article in articles:
            # Combine title and content for analysis
            text = f"{article['title']} {article.get('content', '')}"
            label, score = self.analyze_text(text)

            # Add sentiment results to the article data
            article['sentiment_label'] = label
            article['sentiment_score'] = score
            article['analyzed_at'] = datetime.utcnow()

            analyzed_articles.append(article)

        return analyzed_articles

# Example usage:
if __name__ == "__main__":
    # Sample data input from `news_scraper.py`
    scraped_articles = [
        {
            'title': 'Amazon Reports Shit Q3 Earnings',
            'url': 'https://example.com/article1',
            'content': 'Amazon has reported horrible earnings this quarter, under expectations...'
        },
        {
            'title': 'New Tech Innovations at Amazon',
            'url': 'https://example.com/article2',
            'content': 'Amazon is introducing new tech products to enhance their market share...'
        }
    ]

    analyzer = SentimentAnalyzer()
    analyzed_articles = analyzer.analyze_articles(scraped_articles)

    # Print the output for verification
    for article in analyzed_articles:
        print(f"Title: {article['title']}")
        print(f"Sentiment: {article['sentiment_label']} ({article['sentiment_score']})")
        print(f"URL: {article['url']}\n")