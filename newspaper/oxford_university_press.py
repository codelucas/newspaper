#  <h2 scrollto-destination=23371402 id="23371402" class="abstract-title" >Abstract</h2>
#  <section class="abstract"><p>In the past, refugee camp security has been examined in many lights;
#  however, the demographic make-up of camps has not been focused on. In this article, I present a quantitative
#  model that examines attacks on refugee camps. I argue that the likelihood of an attack on a camp is affected
#  by the demographic make-up of the camp. The primary demographic causes that affect vulnerability are the level
#  of male population of the camp, age of camp residents, and the size of the camp. With the available data,
#  I find that these demographic indicators are significant in determining the likelihood of an attack. Assessing
#  what characteristics of camps and their populations increase the likelihood of an attack should serve as a guide
#  to the implementation and organization of new refugee camps to ensure peace and stability for an already
#  fragile community.</p>
#  </section>

# https://academic.oup.com/robots.txt
# curl https://academic.oup.com/jrs/article-abstract/24/1/23/1595471
# curl: (56) LibreSSL SSL_read: SSL_ERROR_SYSCALL, errno 54


class OxfordUniversityPress:

    # noinspection PyUnresolvedReferences
    def __init__(self, browser):
        # type: (object, str) -> None
        self.browser = browser
        self.domain = "https://academic.oup.com/"
        self.summary = ""

    def get_domain(self):
        return self.domain

    def get_summary(self, url):
        if url.startswith(self.domain):
            self.browser.get(url)
            # https://selenium-python.readthedocs.io/locating-elements.html
            elem = self.browser.find_element_by_class_name('abstract')
            self.summary = elem.text
            return self.summary
        else:
            raise Exception('url must start with {} was: {}'.format(self.domain, url))

