`docker-compose build`

`docker-compose run newspaper-keeeb bash`

Run tests:

Feel free to give our testing suite a shot, everything is mocked!::

    $ python3 tests/unit_tests.py

Planning on tweaking our full-text algorithm? Add the ``fulltext`` parameter::

    $ python3 tests/unit_tests.py fulltext