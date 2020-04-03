# -*- coding: utf-8 -*-
from newspaper.news_ycombinator import parse_html


# noinspection PyUnresolvedReferences
def test_news_ycombinator(fixture_directory):
    test_driver_file = "%s/%s" % (fixture_directory, "news_ycombinator.html")
    with open(test_driver_file, encoding='utf-8') as f:
        html = f.read()
        output = parse_html(html)
        assert (all(isinstance(elem, dict) for elem in output))
