import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from newspaper.oxford_university_press import OxfordUniversityPress
from newspaper.utils import get_driver


# <section class="abstract"><p>In the past, refugee camp security has been examined in many lights; however, the demographic make-up of camps has not been focused on. In this article, I present a quantitative model that examines attacks on refugee camps. I argue that the likelihood of an attack on a camp is affected by the demographic make-up of the camp. The primary demographic causes that affect vulnerability are the level of male population of the camp, age of camp residents, and the size of the camp. With the available data, I find that these demographic indicators are significant in determining the likelihood of an attack. Assessing what characteristics of camps and their populations increase the likelihood of an attack should serve as a guide to the implementation and organization of new refugee camps to ensure peace and stability for an already fragile community.</p></section>
class GoogleScholar:
    # https://www.pingshiuanchua.com/blog/post/scraping-search-results-from-google-search
    ua = UserAgent()

    def get_descriptions(self, scholar_sites):
        # type: (list) -> list
        browser = get_driver()
        oxford_university_press = OxfordUniversityPress(browser)
        for scholar_site in scholar_sites:
            try:
                if scholar_site['link'].startswith(oxford_university_press.get_domain()):
                    scholar_site['summary'] = oxford_university_press.get_summary(scholar_site['link'])
                else:
                    response = requests.get(scholar_site['link'], {'User-Agent': self.ua.random})
                    soup = BeautifulSoup(response.text, 'html.parser')
                    scholar_site['summary'] = soup.find('section', attrs={'class': 'abstract'})
            except Exception as ex:
                print(ex)
        browser.quit()
        return scholar_sites
