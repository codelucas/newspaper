import doctest
import logging
import os
import sys
import tempfile
import traceback
import unittest

import tldextract


def _temporary_file():
    """ Make a writable temporary file and return its absolute path.
    """
    return tempfile.mkstemp()[1]


fake_suffix_list_url = "file://" + os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'fixtures/fake_suffix_list_fixture.dat'
)

extract = tldextract.TLDExtract(cache_file=_temporary_file())
extract_no_cache = tldextract.TLDExtract(cache_file=False)
extract_using_real_local_suffix_list = tldextract.TLDExtract(cache_file=_temporary_file())
extract_using_real_local_suffix_list_no_cache = tldextract.TLDExtract(cache_file=False)
extract_using_fallback_to_snapshot_no_cache = tldextract.TLDExtract(
    cache_file=None,
    suffix_list_url=None
)
extract_using_fake_suffix_list = tldextract.TLDExtract(
    cache_file=_temporary_file(),
    suffix_list_url=fake_suffix_list_url
)
extract_using_fake_suffix_list_no_cache = tldextract.TLDExtract(
    cache_file=None,
    suffix_list_url=fake_suffix_list_url
)


class IntegrationTest(unittest.TestCase):

    def test_log_snapshot_diff(self):
        logging.basicConfig(level=logging.DEBUG)

        extractor = tldextract.TLDExtract()
        try:
            os.remove(extractor.cache_file)
        except (IOError, OSError):
            logging.warning(traceback.format_exc())

        # TODO: if .tld_set_snapshot is up to date, this won't trigger a diff
        extractor('ignore.com')

    def test_bad_kwargs(self):
        self.assertRaises(
            ValueError,
            tldextract.TLDExtract,
            cache_file=False, suffix_list_url=False, fallback_to_snapshot=False
        )

    def test_fetch_and_suffix_list_conflict(self):
        """ Make sure we support both fetch and suffix_list_url kwargs for this version.

        GitHub issue #41.
        """
        extractor = tldextract.TLDExtract(suffix_list_url='foo', fetch=False)
        assert not extractor.suffix_list_url

class ExtractTest(unittest.TestCase):
    def assertExtract(self, expected_subdomain, expected_domain, expected_tld, url,
                      fns=(
                          extract,
                          extract_no_cache,
                          extract_using_real_local_suffix_list,
                          extract_using_real_local_suffix_list_no_cache,
                          extract_using_fallback_to_snapshot_no_cache
                      )):
        for fn in fns:
            ext = fn(url)
            self.assertEquals(expected_subdomain, ext.subdomain)
            self.assertEquals(expected_domain, ext.domain)
            self.assertEquals(expected_tld, ext.tld)

    def test_american(self):
        self.assertExtract('www', 'google', 'com', 'http://www.google.com')

    def test_british(self):
        self.assertExtract("www", "theregister", "co.uk", "http://www.theregister.co.uk")

    def test_no_subdomain(self):
        self.assertExtract("", "gmail", "com", "http://gmail.com")

    def test_nested_subdomain(self):
        self.assertExtract("media.forums", "theregister", "co.uk",
            "http://media.forums.theregister.co.uk")

    def test_odd_but_possible(self):
        self.assertExtract('www', 'www', 'com', 'http://www.www.com')
        self.assertExtract('', 'www', 'com', 'http://www.com')

    def test_local_host(self):
        self.assertExtract('', 'wiki', '', 'http://wiki/')
        self.assertExtract('wiki', 'bizarre', '', 'http://wiki.bizarre')

    def test_qualified_local_host(self):
        self.assertExtract('', 'wiki', 'info', 'http://wiki.info/')
        self.assertExtract('wiki', 'information', '', 'http://wiki.information/')

    def test_ip(self):
        self.assertExtract('', '216.22.0.192', '', 'http://216.22.0.192/')
        self.assertExtract('216.22', 'project', 'coop', 'http://216.22.project.coop/')

    def test_empty(self):
        self.assertExtract('', '', '', 'http://')

    def test_scheme(self):
        self.assertExtract('mail', 'google', 'com', 'https://mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', 'ssh://mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', '//mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', 'mail.google.com/mail', fns=(extract,))

    def test_port(self):
        self.assertExtract('www', 'github', 'com', 'git+ssh://www.github.com:8443/')

    def test_username(self):
        self.assertExtract('1337', 'warez', 'com', 'ftp://johndoe:5cr1p7k1dd13@1337.warez.com:2501')

    def test_query_fragment(self):
        self.assertExtract('', 'google', 'com', 'http://google.com?q=cats')
        self.assertExtract('', 'google', 'com', 'http://google.com#Welcome')
        self.assertExtract('', 'google', 'com', 'http://google.com/#Welcome')
        self.assertExtract('', 'google', 'com', 'http://google.com/s#Welcome')
        self.assertExtract('', 'google', 'com', 'http://google.com/s?q=cats#Welcome')

    def test_regex_order(self):
        self.assertExtract('www', 'parliament', 'uk', 'http://www.parliament.uk')
        self.assertExtract('www', 'parliament', 'co.uk', 'http://www.parliament.co.uk')

    def test_unhandled_by_iana(self):
        self.assertExtract('www', 'cgs', 'act.edu.au', 'http://www.cgs.act.edu.au/')
        self.assertExtract('www', 'google', 'com.au', 'http://www.google.com.au/')

    def test_tld_is_a_website_too(self):
        self.assertExtract('www', 'metp', 'net.cn', 'http://www.metp.net.cn')
        #self.assertExtract('www', 'net', 'cn', 'http://www.net.cn') # This is unhandled by the
        # PSL. Or is it?

    def test_dns_root_label(self):
        self.assertExtract('www', 'example', 'com', 'http://www.example.com./')


class ExtractTestUsingCustomSuffixListFile(unittest.TestCase):
    def test_suffix_which_is_not_in_custom_list(self):
        for fn in (extract_using_fake_suffix_list, extract_using_fake_suffix_list_no_cache):
            result = fn("www.google.com")
            self.assertEquals(result.suffix, "")

    def test_custom_suffixes(self):
        for fn in (extract_using_fake_suffix_list, extract_using_fake_suffix_list_no_cache):
            for custom_suffix in ('foo', 'bar', 'baz'):
                result = fn("www.foo.bar.baz.quux" + "." + custom_suffix)
                self.assertEquals(result.suffix, custom_suffix)


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite(tldextract.tldextract),
        unittest.TestLoader().loadTestsFromTestCase(IntegrationTest),
        unittest.TestLoader().loadTestsFromTestCase(ExtractTest),
        unittest.TestLoader().loadTestsFromTestCase(ExtractTestUsingCustomSuffixListFile),
    ])


def run_tests(stream=sys.stderr):
    suite = test_suite()
    unittest.TextTestRunner(stream).run(suite)


if __name__ == "__main__":
    run_tests()

