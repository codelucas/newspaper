# -*- coding: utf-8 -*-

from newspaper.oxford_university_press import OxfordUniversityPress
# Check if your url end-point actively prevents programmatic access.
#
# Take a look at the robots.txt file in the root directory of a website: http://myweburl.com/robots.txt.
#
# If it contains text that looks like this : User-agent: * Disallow: /
#
# This site doesn’t like and want scraping. This gives you the same dreaded error 54, connection reset by the peer.
from newspaper.utils import get_driver


# noinspection PyUnresolvedReferences
def test_oxford_university_press():
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys

    browser = get_driver()

    # browser.get('http://www.google.com')
    # assert 'Google' in browser.title
    # elem = browser.find_element_by_name('p')  # Find the search box
    # elem.send_keys('seleniumhq' + Keys.RETURN)

    oxford_university_press = OxfordUniversityPress(browser)
    domain = oxford_university_press.get_domain()
    assert domain == "https://academic.oup.com/"
    summary = oxford_university_press.get_summary('https://academic.oup.com/jrs/article-abstract/24/1/23/1595471')
    assert len(summary)
    browser.quit()

    assert oxford_university_press.summary
    assert len(oxford_university_press.summary)
    assert 'refugee camp' in oxford_university_press.summary
