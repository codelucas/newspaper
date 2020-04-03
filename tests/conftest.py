import json
import pytest

# noinspection PyProtectedMember
@pytest.fixture
def fixture_directory():
    import os
    return os.path.join(os.path.dirname(__file__), "fixtures")
