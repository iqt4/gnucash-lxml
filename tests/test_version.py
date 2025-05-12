"""Tests for version identification and formatting."""
from gnucash_lxml import __version__
import re

def test_version_format():
    assert isinstance(__version__, str)
    assert re.match(r'^\d+\.\d+\.\d+', __version__) is not None

def test_version_components():
    """Verify version follows semantic versioning."""
    major, minor, patch = __version__.split('.')[:3]
    assert major.isdigit()
    assert minor.isdigit()
    assert patch.replace('a','').isdigit()  # handles alpha releases

# Contains AI-generated edits.
