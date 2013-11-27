feedparser - Parse Atom and RSS feeds in Python.

Copyright (c) 2010-2013 Kurt McKee <contactme@kurtmckee.org>
Copyright (c) 2002-2008 Mark Pilgrim

feedparser is open source. See the LICENSE file for more information.


Installation
============

Feedparser can be installed using distutils or setuptools by running:

    $ python setup.py install

If you're using Python 3, feedparser will automatically be updated by the 2to3
tool; installation should be seamless across Python 2 and Python 3.

There's one caveat, however: sgmllib.py was deprecated in Python 2.6 and is no
longer included in the Python 3 standard library. Because feedparser currently
relies on sgmllib.py to handle illformed feeds (among other things), it's a
useful library to have installed.

If your feedparser download included a copy of sgmllib.py, it's probably called
sgmllib3.py, and you can simply rename the file to sgmllib.py. It will not be
automatically installed using the command above, so you will have to manually
copy it to somewhere in your Python path.

If a copy of sgmllib.py was not included in your feedparser download, you can
grab a copy from the Python 2 standard library (preferably from the Python 2.7
series) and run the 2to3 tool on it:

    $ 2to3 -w sgmllib.py

If you copied sgmllib.py from a Python 2.6 or 2.7 installation you'll
additionally need to edit the resulting file to remove the `warnpy3k` lines at
the top of the file. There should be four lines at the top of the file that you
can delete.

Because sgmllib.py is a part of the Python codebase, it's licensed under the
Python Software Foundation License. You can find a copy of that license at
python.org:

    http://docs.python.org/license.html


Documentation
=============

The feedparser documentation is available on the web at:

    http://packages.python.org/feedparser

It is also included in its source format, ReST, in the docs/ directory. To
build the documentation you'll need the Sphinx package, which is available at:

    http://sphinx.pocoo.org/

You can then build HTML pages using a command similar to:

    $ sphinx-build -b html docs/ fpdocs

This will produce HTML documentation in the fpdocs/ directory.


Testing
=======

Feedparser has an extensive test suite that has been growing for a decade. If
you'd like to run the tests yourself, you can run the following command:

    $ python feedparsertest.py

This will spawn an HTTP server that will listen on port 8097. The tests will
fail if that port is in use.
