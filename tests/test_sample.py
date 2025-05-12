import pytest
from decimal import Decimal
from gnucash_lxml.models import Book, Account, Transaction

def test_book_properties(sample_gnucash):
    """Test basic Book properties"""
    assert isinstance(sample_gnucash, Book)
    assert sample_gnucash.guid is not None
    assert len(sample_gnucash.accounts) > 0

def test_root_account(sample_gnucash):
    """Test root account properties"""
    root = sample_gnucash.root_account
    assert root.name == "Root Account"
    assert root.type == "ROOT"
    assert root.parent is None

def test_account_tree(sample_gnucash):
    """Test account tree structure"""
    accounts = sample_gnucash.accounts
    # Skip root account
    for account in accounts[1:]:
        assert account.parent is not None
        assert account in account.parent.children