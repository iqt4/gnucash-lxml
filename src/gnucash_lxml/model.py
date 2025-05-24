# model.py --- Data models for GnuCash XML
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid
from lxml import etree
from typing import Any
from .query import (
    GetElement, GetText, GetDate, GetNumber, GetValue
)

# Setup namespace lookup
ns_lookup = etree.ElementNamespaceClassLookup()
gnc_element = ns_lookup.get_namespace('http://www.gnucash.org/XML/gnc')
trn_element = ns_lookup.get_namespace('http://www.gnucash.org/XML/trn')
none_element = ns_lookup.get_namespace(None)

# Register namespace for commodities as they don't have a guid
NAMESPACE_CMDTY = uuid.uuid4()

@gnc_element('book')
class Book(etree.ElementBase):
    """
    A book is the main container for GnuCash data.
    <gnc:book/>

    XML Structure:
        book:id          -> guid (str): Unique identifier
        book:slots       -> slots (Slots): Additional information
        gnc:commodity    -> commodities (list[Commodity]): Available commodities
        gnc:account      -> accounts (list[Account]): Chart of accounts
        gnc:transaction  -> transactions (list[Transaction]): Financial transactions
        gnc:pricedb      -> prices (list[Prices]): Price database

    Not Implemented:
        - gnc:schedxaction: Scheduled transactions
        - gnc:template-transactions: Transaction templates
        - gnc:count-data: Data counts
        - book:slots: Detailed slot elements
    """
    # Simple attributes using descriptors
    guid = GetText('book:id')

    # Internal XML elements
    _slots_element = GetElement('book:slots')
    _pricedb_element = GetElement('gnc:pricedb')

    def _init(self):
        """Initialize book and build index of objects"""
        self._index = {}
        self._commodities = self.findall('gnc:commodity', self.nsmap)
        self._accounts = self.findall('gnc:account', self.nsmap)
        self._transactions = self.findall('gnc:transaction', self.nsmap)
        self._prices = None

    def __repr__(self):
        return f"<Book {self.guid}>"

    def _find_commodity(self, obj: etree.ElementBase, path: str) -> Any:
        """ Find a commodity in the book by its generated GUID from space and symbol. """
        o = obj.find(path, namespaces=obj.nsmap)
        if o is not None:
            c_space = o.findtext('cmdty:space', namespaces=o.nsmap)
            c_symbol = o.findtext('cmdty:id', namespaces=o.nsmap)
            guid = uuid.uuid5(NAMESPACE_CMDTY, f"{c_space}:{c_symbol}").hex
            c_obj = self._index.get(guid)
            if c_obj is None:
                raise ValueError(f"Commodity {c_space}:{c_symbol} not found.")
            return c_obj
        
    def _find_account(self, obj: etree.ElementBase, path: str) -> Any:
        """Find an account in the book by GUID."""
        o = obj.find(path, namespaces=obj.nsmap)
        if o is not None:
            guid = o.text
            a_obj = self._index.get(guid)
            if a_obj is None:
                raise ValueError(f"Account {guid} not found.")
            return a_obj

    # Public properties
    @property
    def commodities(self):
        """List of all commodities in the book"""
        return self._commodities

    @property
    def root_account(self):
        """Root account of the account hierarchy"""
        return self._accounts[0]

    @property
    def accounts(self):
        """List of all accounts in the book"""
        return self._accounts

    @property
    def transactions(self):
        """List of all transactions in the book"""
        return self._transactions

    @property
    def slots(self):
        """Additional book information stored in slots"""
        return self._slots_element

    @property
    def prices(self):
        """
        Price database with lazy loading of price entries.
        Returns list of Price objects.
        """
        if self._prices is None and self._pricedb_element is not None:
            self._prices = self._pricedb_element.findall('price', namespaces=self.nsmap)
        return self._prices or []

    def walk(self):
        """Walk the account tree starting from root account"""
        return self.root_account.walk()    


@gnc_element('commodity')
class Commodity(etree.ElementBase):
    """
    A commodity represents a tradeable item (currency, stock, mutual fund, etc.).
    <gnc:commodity/>

    XML Structure:
        cmdty:space    -> space (str): Namespace (e.g. 'CURRENCY', 'NYSE')
        cmdty:id       -> symbol (str): Symbol identifier (e.g. 'EUR', 'AAPL')
        cmdty:name     -> name (str): Full name (optional)
        cmdty:xcode    -> xcode (str): Alternative code (optional)
        cmdty:fraction -> fraction (str): Smallest fraction (optional)
        cmdty:quote_source   -> source (str): Price quote source (optional)
        cmdty:get_quotes -> get_quotes (str): Enable quote fetching (optional)
        cmdty:quote_tz  -> quote_tz (str): Timezone for quotes (optional)
        cmdty:slots    -> slots (ElementBase): Additional information (optional)

    Not Implemented:
        - cmdty:get_quotes  Optional quote fetching flag
        - cmdty:quote_tz    Optional quote timezone
        - cmdty:source      Optional price source
        - cmdty:fraction    Optional fraction specification
        - cmdty:slots       Optional slot elements for additional information
    """
    # Simple attributes using descriptors
    space = GetText('cmdty:space')
    symbol = GetText('cmdty:id')
    name = GetText('cmdty:name')
    xcode = GetText('cmdty:xcode')

    def _init(self):
        """Initialize commodity and register it in book's index"""
        book = self.getparent()
        book._index.setdefault(self.guid, self)

    def __repr__(self):
        return f"<Commodity {self.space}:{self.symbol}>"
    
    @property
    def guid(self):
        """
        Generate a unique identifier for the commodity.
        The GUID is derived from namespace and symbol since commodities
        don't have GUIDs in the XML file.
        """
        return uuid.uuid5(NAMESPACE_CMDTY, f"{self.space}:{self.symbol}").hex


@none_element('price')
class Price(etree.ElementBase):
    """
    A price represents the value of a commodity in terms of a currency at a specific date.
    <gnc:price/>

    XML Structure:
        price:id       -> guid (str): Unique identifier
        price:commodity -> commodity (Commodity): The commodity being priced
        price:currency -> currency (Commodity): The currency used for pricing
        price:time     -> date (datetime): Date of the price quote
        price:value    -> value (Decimal): The price value
        price:type     -> type (str): Price type (optional)
        price:source   -> source (str): Source of price data (optional)

    Not Implemented:
        - price:type   Optional price type
        - price:source Optional source information
    """
    # Simple attributes using descriptors
    guid = GetText('price:id')
    date = GetDate('price:time/ts:date')
    value = GetNumber('price:value')

    def __repr__(self):
        return f"<Price {self.date:%Y-%m-%d} {self.commodity}/{self.currency}: {self.value}>"

    @property
    def commodity(self):
        """The commodity being priced"""
        book = self.getparent().getparent()
        return book._find_commodity(self, 'price:commodity')

    @property
    def currency(self):
        """The currency in which the price is expressed"""
        book = self.getparent().getparent()
        return book._find_commodity(self, 'price:currency')
    

@gnc_element('account')
class Account(etree.ElementBase):
    """
    An account is part of a tree structure of accounts and contains splits.
    <gnc:account/>

    XML Structure:
        act:name          -> name (str): Account name
        act:id            -> guid (str): Unique identifier
        act:type          -> type (str): Account type (ASSET, LIABILITY, etc)
        act:commodity     -> commodity (Commodity): Account's commodity/currency
        act:commodity-scu -> commodity_scu (str): Smallest commodity unit
        act:description   -> description (str): Account description
        act:parent        -> parent_guid (str): Parent account's GUID
        act:slots         -> slots (ElementBase): Additional information

    Not Implemented:
        - None (all elements from XML spec are implemented)
        - act:slots (detailed slot elements)
    """

    name = GetText('act:name')
    guid = GetText('act:id')
    type = GetText('act:type')
    description = GetText('act:description')
    commodity_scu = GetText('act:commodity-scu')
    parent_guid = GetText('act:parent')

    # Internal XML elements
    _slots_element = GetElement('act:slots')

    def _init(self):
        """Initialize account and register it in book's index"""
        book = self.getparent()
        book._index.setdefault(self.guid, self)

    def __repr__(self):
        return f'<Account {self.name}>'
    
    @property
    def commodity(self):
        book = self.getparent()
        return book._find_commodity(self, 'act:commodity')
    
    @property
    def parent(self):
        book = self.getparent()
        return book._find_account(self, 'act:parent')

    @property
    def children(self):
        """List of child accounts"""
        book = self.getparent()
        expr = './gnc:account[act:parent/text() = $guid]'
        return book.xpath(expr, guid=self.guid, namespaces=self.nsmap)

    @property
    def splits(self):
        """List of splits posted to this account"""
        book = self.getparent()
        expr = './gnc:transaction/trn:splits/trn:split[split:account/text() = $guid]'
        return book.xpath(expr, guid=self.guid, namespaces=self.nsmap)
        # expr = '/gnc-v2/gnc:book/gnc:transaction/trn:splits/trn:split/split:account[text() = $guid]/parent::*'
        # return self.xpath(expr, guid=self.guid, namespaces=self.nsmap)

    @property
    def slots(self):
        """Additional account information stored in slots"""
        return self._slots_element

    @property
    def fullname(self):
        """Full hierarchical account name separated by colons"""
        if self.parent is not None:
            pfn = self.parent.fullname
            if pfn:
                return f'{pfn}:{self.name}'
            else:
                return self.name
        else:
            return ''

    def walk(self):
        """
        Generate splits in this account tree by walking the tree.

        For each account, it yields a 3-tuple (account, sub_accounts, splits).

        You can modify the list of sub_accounts, but should not modify
        the list of splits.
        """
        accounts = [self]
        while accounts:
            acc, accounts = accounts[0], accounts[1:]
            children = list(acc.children)
            yield acc, children, acc.splits
            accounts.extend(children)


@gnc_element('transaction')
class Transaction(etree.ElementBase):
    """
    A transaction is a balanced group of splits.
    <gnc:transaction/>

    XML Structure:
        trn:id              -> guid (str): Unique identifier
        trn:num            -> num (str): Transaction number
        trn:currency       -> currency (Commodity): Transaction currency
        trn:date-posted    -> date (datetime): Date when transaction was posted
        trn:date-entered   -> date_entered (datetime): Date when entered into system
        trn:description    -> description (str): Transaction description
        trn:splits         -> splits (list[Split]): List of transaction splits
        trn:slots         -> slots (Slots): Additional information

    Not Implemented:
        - None (all elements from XML spec are implemented)
        - trn:slots (detailed slot elements)
    """
    # Simple attributes using descriptors
    guid = GetText('trn:id')
    num = GetText('trn:num')
    date = GetDate('trn:date-posted/ts:date')
    date_entered = GetDate('trn:date-entered/ts:date')
    description = GetText('trn:description')

    # Internal XML elements
    _splits_element = GetElement('trn:splits')
    _slots_element  = GetElement('trn:slots')

    def __repr__(self):
        return f"<Transaction {self.guid} on {self.date}: {self.description}>"
    
    @property
    def currency(self):
        book = self.getparent()
        return book._find_commodity(self, 'trn:currency')
    
    @property
    def splits(self):
        """Lazy loads the transaction's splits"""
        if self._splits_element is not None:
            return self._splits_element.findall('trn:split', namespaces=self.nsmap)
        return []

    @property
    def slots(self):
        """Access to slot information"""
        return self._slots_element


@trn_element('split')
class Split(etree.ElementBase):
    """
    A split is one entry in a transaction.
    <trn:split/>

    XML Structure:
        split:id              -> guid (str): Unique identifier
        split:memo           -> memo (str): Split memo/description
        split:reconciled-state -> reconciled_state (str): Reconciliation status
        split:reconcile-date  -> reconcile_date (datetime): Date of reconciliation
        split:value          -> value (Decimal): Value in transaction currency
        split:quantity       -> quantity (Decimal): Amount in account commodity
        split:action         -> action (str): Type of action
        split:account        -> account (Account): Reference to account
        split:slots         -> slots (ElementBase): Additional information

    Not Implemented:
        - split:lot          Optional lot information
        - split:slots        Detailed slot elements
    """

    guid = GetText('split:id')
    memo = GetText('split:memo')
    reconciled_state = GetText('split:reconciled-state')
    reconcile_date = GetDate('split:reconcile-date/ts:date')
    value = GetNumber('split:value')
    quantity = GetNumber('split:quantity')
    action = GetText('split:action')

    # Internal XML elements
    _slots_element = GetElement('split:slots')

    @property
    def transaction(self):
        return self.getparent()

    def __repr__(self):
        return f"<Split {self.transaction.date} '{self.account}' {self.value}>"
    
    @property
    def account(self):
        book = self.transaction.getparent()
        return book._find_account(self, 'split:account')
    
    @property
    def slots(self):
        """Access to slot information"""
        return self._slots_element


@none_element('slot')
class Slot(etree.ElementBase):
    """
    A slot contains all kind of information.
    <slot/>
    """
    key = GetText('slot:key')
    value = GetValue('slot:value')

    def __repr__(self):
        return f"<Slot {self.key}:{self.value}>"