import pytest
from pathlib import Path
from gnucash_lxml import load

# We open the sample.gnucash file ONCE per test session
# Background: GetAccount and GetCommodity ahave global (class-level) dictionaries
# that are used to cache the objects. This is done to avoid
# having to search the entire XML tree for each object.
@pytest.fixture()
def data_dir() -> Path:
    """Return path to test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture()
def sample_gnucash(data_dir):
    """Return loaded sample GnuCash book"""
    return load(data_dir / "sample.gnucash")