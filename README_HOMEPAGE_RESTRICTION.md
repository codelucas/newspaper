# Homepage URL Restriction Feature

## Overview

This feature allows you to limit article scraping to only URLs that appear directly on a news source's homepage, rather than crawling the entire site structure. This is useful for sites like Reuters where you only want to extract articles currently featured on the homepage.

## Usage

```python
import newspaper

# Normal usage (crawls entire site structure)
reuters = newspaper.build('https://www.reuters.com')

# Restricted to only homepage URLs
reuters_homepage = newspaper.build(
    'https://www.reuters.com',
    restrict_to_homepage_urls=True
)

print(f"All articles: {len(reuters.articles)}")
print(f"Homepage articles: {len(reuters_homepage.articles)}")
```

## How It Works

1. The `build()` function accepts a new `restrict_to_homepage_urls` parameter (default: False)
2. When set to True, the Source object extracts all URLs from `<a href>` tags on the homepage
3. After article generation, the articles list is filtered to include only those with URLs matching the homepage links
4. This significantly reduces the number of articles processed, focusing only on currently featured content

## Example Results

When scraping Reuters:
- Normal mode: ~1000+ articles (crawls archives, categories, etc.)
- Homepage restricted: ~200-300 articles (only what's visible on the homepage)

## Performance Benefits

- Faster processing (fewer articles to download and parse)
- More focused results (only current/featured articles)
- Reduced server load (fewer requests)
- Better control over what content is scraped

## Running the Demo

A demonstration script is included to show the difference between normal and restricted modes:

```
python test_homepage_restriction.py [optional_url]
```

The script will show articles counts for both methods and process a sample of the homepage articles.

## Testing

A test case for this feature is included in `tests/test_reuters.py`. Run it with:

```
python -m unittest tests/test_reuters.py
```

## Acknowledgments

This feature was developed in response to [GitHub issue #455](https://github.com/codelucas/newspaper/issues/455) to provide better control over article scraping scope.
