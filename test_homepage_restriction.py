#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demonstration script for the restrict_to_homepage_urls feature.

This script shows how to use the new feature to scrape only articles
listed on a news site's homepage rather than crawling the entire site.
"""

import os
import sys
import time
import newspaper
from newspaper import Article


def print_article_info(article, index):
    """Print basic information about an article"""
    print(f"\n[{index}] {article.title}")
    print(f"URL: {article.url}")
    print(f"Published: {article.publish_date}")
    print(f"Summary: {article.summary[:150]}..." if article.summary else "No summary available")


def save_to_file(articles, filename):
    """Save article information to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Total articles: {len(articles)}\n\n")
        for i, article in enumerate(articles, 1):
            f.write(f"[{i}] {article.title}\n")
            f.write(f"URL: {article.url}\n")
            f.write(f"Published: {article.publish_date}\n")
            f.write(f"Summary: {article.summary[:200]}...\n" if article.summary else "No summary available\n")
            f.write("-" * 80 + "\n\n")
    print(f"Saved {len(articles)} articles to {filename}")


def main():
    # Set up output directory
    output_dir = "reuters_articles"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.reuters.com"

    print(f"Scraping articles from {url}...")

    # First, demonstrate normal behavior (crawls entire site)
    start_time = time.time()
    print("\nBuilding source WITHOUT homepage restriction...")
    news_unrestricted = newspaper.build(url, memoize_articles=False, fetch_images=False, number_threads=1)
    print(f"Found {len(news_unrestricted.articles)} articles without restriction")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")

    # Now demonstrate the new feature
    start_time = time.time()
    print("\nBuilding source WITH homepage restriction...")
    news_restricted = newspaper.build(
        url, 
        restrict_to_homepage_urls=True,
        memoize_articles=False, 
        fetch_images=False,
        number_threads=1
    )
    print(f"Found {len(news_restricted.articles)} articles with homepage restriction")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")

    # Download and process restricted articles
    print("\nDownloading and processing homepage articles...")
    processed_count = 0
    successful_articles = []

    for i, article in enumerate(news_restricted.articles[:20], 1):  # Process up to 20 articles
        try:
            print(f"Processing article {i}/{min(20, len(news_restricted.articles))}...")
            article.download()
            article.parse()
            article.nlp()
            processed_count += 1
            successful_articles.append(article)
            print_article_info(article, i)
        except Exception as e:
            print(f"Error processing article {i}: {e}")

    print(f"\nSuccessfully processed {processed_count} articles")

    # Save results to file
    if successful_articles:
        save_to_file(successful_articles, os.path.join(output_dir, "homepage_articles.txt"))


if __name__ == "__main__":
    main()
