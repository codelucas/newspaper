# -*- coding: utf-8 -*-

"""
Test the homepage URL restriction feature with Reuters website.
"""

import unittest
import re
import requests
from bs4 import BeautifulSoup
from newspaper import build
from newspaper.article import Article


class TestReutersScraper(unittest.TestCase):
    def test_restrict_to_homepage_urls(self):
        """Test that only URLs from the Reuters homepage are processed when restrict_to_homepage_urls=True"""
        # Skip this test if Reuters is not accessible
        try:
            requests.get("https://www.reuters.com", timeout=5)
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            self.skipTest("Reuters website not accessible")

        # Build the source with restricted URLs
        news = build("https://www.reuters.com", 
                    restrict_to_homepage_urls=True, 
                    memoize_articles=False,
                    fetch_images=False,
                    number_threads=1)

        # Verify we have a reasonable number of articles (not too many, not too few)
        # Count may vary based on Reuters homepage changes
        self.assertLessEqual(news.size(), 500, "Too many articles scraped")
        self.assertGreater(news.size(), 50, "Too few articles scraped")

        # Check if article URLs look like Reuters article URLs
        article_pattern = re.compile(r'^https://www\.reuters\.com/.*')
        for article in news.articles[:10]:  # Check first 10 articles
            self.assertTrue(
                article_pattern.match(article.url),
                f"Invalid article URL: {article.url}"
            )

    def test_manual_homepage_extraction(self):
        """Test a manual process to extract and process homepage URLs"""
        # Skip this test if Reuters is not accessible
        try:
            resp = requests.get("https://www.reuters.com", timeout=5)
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            self.skipTest("Reuters website not accessible")

        # Parse homepage HTML to extract article URLs
        soup = BeautifulSoup(resp.text, 'html.parser')
        homepage_urls = set()

        # Extract and normalize article URLs from <a> tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                href = "https://www.reuters.com" + href
            if re.match(r'^https://www\.reuters\.com/.*', href) and \
               not re.search(r'/(video|gallery|slideshow)/', href):
                homepage_urls.add(href)

        # Verify we found a reasonable number of URLs
        self.assertGreater(len(homepage_urls), 50, "Too few URLs found on homepage")
        self.assertLess(len(homepage_urls), 500, "Too many URLs found on homepage")

        # Process a small sample of URLs
        sample_size = min(5, len(homepage_urls))
        processed = 0

        for url in list(homepage_urls)[:sample_size]:
            try:
                article = Article(url, language='en', fetch_images=False)
                article.download()
                article.parse()
                article.nlp()
                self.assertTrue(article.title, f"No title for {url}")
                self.assertTrue(article.text.strip(), f"No text for {url}")
                processed += 1
            except Exception as e:
                print(f"Error processing {url}: {e}")

        # Verify we processed the expected number of articles
        self.assertEqual(processed, sample_size, "Failed to process all sample articles")


if __name__ == '__main__':
    unittest.main()
