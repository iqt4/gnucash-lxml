import pytest
from decimal import Decimal
from gnucash_lxml.model import Book, Account, Transaction, Commodity

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
    for account in accounts:
        assert isinstance(account, Account)
        if account.type != "ROOT":
            assert account.guid is not None
            assert account.name is not None
            assert account.commodity is not None
            # Check if the account has a parent
            if account.parent_guid:
                assert isinstance(account.parent, Account)
                assert account.parent.guid == account.parent_guid
            else:
                assert account.parent is None
            assert account in account.parent.children

def test_commodity_instances(sample_gnucash):
    """Loop over all commodities and assert each is a Commodity instance."""
    for comm in sample_gnucash.commodities:
        assert isinstance(comm, Commodity)

def test_transaction_instances(sample_gnucash):
    """Test that all transactions are Transaction instances and have valid properties."""
    for txn in sample_gnucash.transactions:
        assert isinstance(txn, Transaction)
        assert txn.guid is not None
        assert txn.currency is not None
        assert hasattr(txn, 'splits')
        assert len(txn.splits) > 0

def test_transaction_splits_balanced(sample_gnucash):
    """Test that all transactions have balanced splits (sum to zero)."""
    for txn in sample_gnucash.transactions:
        # Sum up all split values in the transaction
        split_sum = sum(Decimal(split.value) for split in txn.splits)
        # The sum should be zero (balanced transaction)
        assert split_sum == 0, f"Transaction {txn.guid} is not balanced: sum={split_sum}"

def test_pricedb_entries(sample_gnucash):
    """Test that the pricedb contains valid price entries."""
    for price in sample_gnucash.prices:
        assert hasattr(price, "value")
        assert hasattr(price, "date")
        assert isinstance(price.commodity, Commodity)
        assert isinstance(price.currency, Commodity)
        assert price.value is not None
        assert price.date is not None

# Contains AI-generated edits.