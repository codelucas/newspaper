import requests
import json
from googleapiclient.discovery import build  # Import the library
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


# https://towardsdatascience.com/current-google-search-packages-using-python-3-7-a-simple-tutorial-3606e459e0d4
class GoogleSearch:
    api_key = "AIzaSyDutwc5PeWro1HiEl0dF3a99ys6FoTW-_A"  # "my-secret-api-key"
    cse_id = "008091217464715917519:ttamceevq13"  # "my-secret-custom-search-id
    # https://www.pingshiuanchua.com/blog/post/scraping-search-results-from-google-search
    ua = UserAgent()

    def get_search_urls(self, query, number_of_search_results_return):
        # type: (str, number_of_search_results_return) -> list

        """Google Custom Search enables you to create a search engine for your website, your blog, or a collection
           of websites. You can configure your engine to search both web pages and images

        :param query: data with coordinates
            :type:string
            :example:
                "child AND soldiers"
        :param number_of_search_results_return: 
            :type: integer
            :example:
                a value [1..10]
        :return: list of urls
        """
        query_service = build("customsearch", "v1", developerKey=self.api_key)
        kwargs = {
            'num': number_of_search_results_return
        }
        # https://developers.google.com/custom-search/v1/cse/list
        query_results = query_service.cse().list(q=query,  # Query
                                                 cx=self.cse_id,  # CSE ID
                                                 **kwargs
                                                 ).execute()
        my_google_urls = []
        for result in query_results['items']:
            my_google_urls.append(result['link'])
        return my_google_urls

    #  <tr class="gsc_a_tr">,
    #     <td class="gsc_a_t">,
    #        <a href="javascript:void(0)"
    #           data-href="/citations?view_op=view_citation&amp;hl=en&amp;user=A5NhLJkAAAAJ&amp;citation_for_view=A5NhLJkAAAAJ:TQgYirikUcIC"
    #           class="gsc_a_at">The rites of the child: Global discourses of youth and reintegrating child soldiers in Sierra Leone</a>,
    #        <div class="gs_gray">S Shepler</div>,
    #        <div class="gs_gray">Journal of Human Rights 4 (2), 197-211<span class="gs_oph">, 2005</span></div>,
    #     </td>,
    #     <td class="gsc_a_c"><a href="https://scholar.google.com/scholar?oi=bibs&amp;hl=en&amp;cites=17455492728027388341"
    #                            class="gsc_a_ac gs_ibl">156</a>
    #     </td>,
    #     <td class="gsc_a_y"><span class="gsc_a_h gsc_a_hc gs_ibl">2005</span></td>,
    #  </tr>,
    def get_sections(self, google_search_urls, html_tag, attrs):
        # type: (list, str, dict) -> list

        if len(google_search_urls):
            for google_search_url in google_search_urls:
                response = requests.get(google_search_url, {'User-Agent': self.ua.random})
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.find_all(html_tag, attrs)
        else:
            return []

    def get_scholar_urls(self, google_search_urls):
        # type: (list) -> list

        # https://www.pingshiuanchua.com/blog/post/scraping-search-results-from-google-search
        attrs = {'class': 'gsc_a_tr'}
        trs = self.get_sections(google_search_urls, 'tr', attrs)
        sites = list()
        for tr in trs:
            # Checks if each element is present, else, raise exception
            try:
                td = tr.find('td', attrs={'class': 'gsc_a_t'})
                title = td.find('a', href=True).get_text()

                td = tr.find('td', attrs={'class': 'gsc_a_c'})
                link = td.find('a', href=True)

                # Check to make sure everything is present before appending to lists
                if link != '' and link['href'] != '' and title != '':
                    sites.append({'title': title, 'link': link['href']})
            # Next loop if one element is not present
            except Exception as ex:
                print(json.dumps(ex, sort_keys=True, indent=4))
        return sites
