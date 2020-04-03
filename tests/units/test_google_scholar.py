# -*- coding: utf-8 -*-

from newspaper.google_scholar import GoogleScholar

# Check if your url end-point actively prevents programmatic access.
#
# Take a look at the robots.txt file in the root directory of a website: http://myweburl.com/robots.txt.
#
# If it contains text that looks like this : User-agent: * Disallow: /
#
# This site doesn’t like and want scraping. This gives you the same dreaded error 54, connection reset by the peer.


# noinspection PyUnresolvedReferences
def test_google_scholar():
    google_scholar = GoogleScholar()
    scholar_sites = [
        {
            'title': 'Refugee Camp Security: Decreasing Vulnerability Through Demographic Controls',
            'link': 'https://academic.oup.com/jrs/article-abstract/24/1/23/1595471'
        }
    ]
    scholar_sites = google_scholar.get_descriptions(scholar_sites)
    for scholar_site in scholar_sites:
        assert scholar_site['summary']
