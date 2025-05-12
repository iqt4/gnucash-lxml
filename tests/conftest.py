import pytest
from pathlib import Path
from gnucash_lxml import load

@pytest.fixture
def data_dir() -> Path:
    """Return path to test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_gnucash(data_dir):
    """Return loaded sample GnuCash book"""
    return load(data_dir / "sample.gnucash")