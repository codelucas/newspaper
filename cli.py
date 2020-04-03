#!/usr/bin/env python3

import datetime
import json
from itertools import repeat
from multiprocessing import Pool, cpu_count
from time import sleep, time

from scrapers.model.google_scholar import GoogleScholar
from scrapers.model.google_search import GoogleSearch
from scrapers.model.news_ycombinator import connect_to_base, parse_html, write_to_file
from scrapers.utils import get_driver


def run_process(page_number, output_filename):
    browser = get_driver()
    if connect_to_base(browser, page_number):
        sleep(2)
        html = browser.page_source
        output_list = parse_html(html)
        write_to_file(output_list, output_filename)
    else:
        print('Error connecting to hackernews')
    browser.quit()


def run_google_scholar_search():
    google_search = GoogleSearch()
    google_search_urls = google_search.get_search_urls("child AND soldiers", 10)
    print(json.dumps(google_search_urls, sort_keys=True, indent=4))
    scholar_sites = google_search.get_scholar_urls(google_search_urls)
    print(json.dumps(scholar_sites, sort_keys=True, indent=4))
    google_scholar = GoogleScholar()
    scholar_sites = google_scholar.get_descriptions(scholar_sites)
    print(json.dumps(scholar_sites, sort_keys=True, indent=4))


if __name__ == '__main__':
    # set variables
    start_time = time()
    output_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    output_filename = f'output_{output_timestamp}.csv'
    # scrape and crawl
    with Pool(cpu_count() - 1) as p:
        p.starmap(run_process, zip(range(1, 21), repeat(output_filename)))
    p.close()
    p.join()
    end_time = time()
    elapsed_time = end_time - start_time
    print(f'Elapsed run time: {elapsed_time} seconds')
