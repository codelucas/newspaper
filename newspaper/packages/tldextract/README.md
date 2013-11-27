# Python Module

`tldextract` accurately separates the gTLD or ccTLD (generic or country code
top-level domain) from the registered domain and subdomains of a URL. For
example, say you want just the 'google' part of 'http://www.google.com'.

*Everybody gets this wrong.* Splitting on the '.' and taking the last 2
elements goes a long way only if you're thinking of simple e.g. .com
domains. Think parsing
[http://forums.bbc.co.uk](http://forums.bbc.co.uk) for example: the naive
splitting method above will give you 'co' as the domain and 'uk' as the TLD,
instead of 'bbc' and 'co.uk' respectively.

`tldextract` on the other hand knows what all gTLDs and ccTLDs look like by
looking up the currently living ones according to
[the Public Suffix List](http://www.publicsuffix.org). So,
given a URL, it knows its subdomain from its domain, and its domain from its
country code.

    >>> import tldextract
    >>> tldextract.extract('http://forums.news.cnn.com/')
    ExtractResult(subdomain='forums.news', domain='cnn', suffix='com')
    >>> tldextract.extract('http://forums.bbc.co.uk/') # United Kingdom
    ExtractResult(subdomain='forums', domain='bbc', suffix='co.uk')
    >>> tldextract.extract('http://www.worldbank.org.kg/') # Kyrgyzstan
    ExtractResult(subdomain='www', domain='worldbank', suffix='org.kg')

`ExtractResult` is a namedtuple, so it's simple to access the parts you want.

    >>> ext = tldextract.extract('http://forums.bbc.co.uk')
    >>> ext.domain
    'bbc'
    >>> '.'.join(ext[:2]) # rejoin subdomain and domain
    'forums.bbc'

This module started by implementing the chosen answer from [this StackOverflow question on
getting the "domain name" from a URL](http://stackoverflow.com/questions/569137/how-to-get-domain-name-from-url/569219#569219).
However, the proposed regex solution doesn't address many country codes like
com.au, or the exceptions to country codes like the registered domain
parliament.uk. The Public Suffix List does, and so does this module.

## Installation

Latest release on PyPI:

    $ pip install tldextract

Or the latest dev version:

    $ pip install -e git://github.com/john-kurkowski/tldextract.git#egg=tldextract

Command-line usage, splits the url components by space:

    $ tldextract http://forums.bbc.co.uk
    forums bbc co.uk

Run tests:

    $ python -m tldextract.tests.all

## Note About Caching & Advanced Usage

Beware when first running the module, it updates its TLD list with a live HTTP
request. This updated TLD set is cached indefinitely in
`/path/to/tldextract/.tld_set`.

(Arguably runtime bootstrapping like that shouldn't be the default behavior,
like for production systems. But I want you to have the latest TLDs, especially
when I haven't kept this code up to date.)

To avoid this fetch or control the cache's location, use your own extract
callable by setting TLDEXTRACT_CACHE environment variable or by setting the
cache_file path in TLDExtract initialization.

    # extract callable that falls back to the included TLD snapshot, no live HTTP fetching
    no_fetch_extract = tldextract.TLDExtract(suffix_list_url=False)
    no_fetch_extract('http://www.google.com')

    # extract callable that reads/writes the updated TLD set to a different path
    custom_cache_extract = tldextract.TLDExtract(cache_file='/path/to/your/cache/file')
    custom_cache_extract('http://www.google.com')

    # extract callable that doesn't use caching
    no_cache_extract = tldextract.TLDExtract(cache_file=False)
    no_cache_extract('http://www.google.com')

If you want to stay fresh with the TLD definitions--though they don't change
often--delete the cache file occasionally, or run

    tldextract --update

or:

    env TLDEXTRACT_CACHE="~/tldextract.cache" tldextract --update

It is also recommended to delete the file after upgrading this lib.

### Specifying your own URL or file for the Suffix List data

You can specify your own input data in place of the default Mozilla Public Suffix List:

    extract = tldextract.TLDExtract(
        suffix_list_url="http://foo.bar.baz",
        # Recommended: Specify your own cache file, to minimize ambiguities about where
        # tldextract is getting its data, or cached data, from.
        cache_file='/path/to/your/cache/file')

The above snippet will fetch from the URL *you* specified, upon first need to download the
suffix list (i.e. if the cache_file doesn't exist).

If you want to use input data from your local filesystem, just use the `file://` protocol:

    extract = tldextract.TLDExtract(
        suffix_list_url="file://absolute/path/to/your/local/suffix/list/file",
        cache_file='/path/to/your/cache/file')

Use an absolute path when specifying the `suffix_list_url` keyword argument. `os.path` is your
friend.

# Public API

I know it's just one method, but I've needed this functionality in a few
projects and programming languages, so I've uploaded
[`tldextract` to App Engine](http://tldextract.appspot.com/). It's there on
GAE's free pricing plan until Google cuts it off. Just hit it with
your favorite HTTP client with the URL you want parsed like so:

    $ curl "http://tldextract.appspot.com/api/extract?url=http://www.bbc.co.uk/foo/bar/baz.html"
    {"domain": "bbc", "subdomain": "www", "suffix": "co.uk"}

