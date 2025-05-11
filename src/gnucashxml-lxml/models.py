# models.py --- Data models for GnuCash XML
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

from lxml import etree
from .query import (
    GetElement, GetText, GetDate, GetNumber, GetValue, GetCommodity, GetAccount
)

# Setup namespace lookup
ns_lookup = etree.ElementNamespaceClassLookup()
gnc_element = ns_lookup.get_namespace('http://www.gnucash.org/XML/gnc')
trn_element = ns_lookup.get_namespace('http://www.gnucash.org/XML/trn')
none_element = ns_lookup.get_namespace(None)

@gnc_element('book')
class Book(etree.ElementBase):
    """
    A book is the main container for GnuCash data.

    It doesn't really do anything at all by itself, except to have
    a reference to the accounts, transactions, prices, and commodities.
    <gnc:book/>
    """

    # Not implemented:
    # - gnc:schedxaction
    # - gnc:template-transactions
    # - gnc:count-data

    guid = GetText('book:id')
    prices = GetElement('gnc:pricedb')
    slots = GetElement('book:slots')

    def _init(self):
        self._commodities = self.findall('gnc:commodity', self.nsmap)
        self._accounts = self.findall('gnc:account', self.nsmap)
        self._transactions = self.findall('gnc:transaction', self.nsmap)

    def __repr__(self):
        return f"<Book {self.guid}>"

    @property
    def commodities(self):
        return self._commodities

    @property
    def root_account(self):
        return self._accounts[0]

    @property
    def accounts(self):
        return self._accounts

    @property
    def transactions(self):
        return self._transactions

    def walk(self):
        return self.root_account.walk()


@gnc_element('commodity')
class Commodity(etree.ElementBase):
    """
    A commodity is something that's stored in GnuCash accounts.
    The key consists of a namespace (space) and a symbol (id).
    """
    # Not implemented:
    # - cmdty:get_quotes => unknown, empty, optional
    # - cmdty:quote_tz => unknown, empty, optional
    # - cmdty:source => text, optional, e.g. "currency"
    # - cmdty:fraction => optional, e.g. "1"

    space = GetText('./cmdty:space')
    symbol = GetText('./cmdty:id')
    name = GetText('./cmdty:name')
    xcode = GetText('./cmdty:xcode')

    def _init(self):
        GetCommodity.register(self)

    def __repr__(self):
        return f"<Commodity {self.space}:{self.symbol}>"


@gnc_element('price')
class Price(etree.ElementBase):
    """
    A price is GnuCash record of the price of a commodity against a currency
    Consists of date, currency, commodity,  value
    <gnc:pricedb/>
    """

    guid = GetText('price:id')
    commodity = GetCommodity('price:commodity')
    currency = GetCommodity('price:currency')
    date = GetDate('price:time/ts:date')
    value = GetNumber('price:value')

    def __repr__(self):
        return f"<Price {self.date:%Y/%m/%d}: {self.value} {self.commodity}/{self.currency} >"


@gnc_element('account')
class Account(etree.ElementBase):
    """
    An account is part of a tree structure of accounts and contains splits.
    <gnc:account/>
    """

    name = GetText('act:name')
    guid = GetText('act:id')
    type = GetText('act:type')
    description = GetText('act:description')
    commodity_scu = GetText('act:commodity-scu')
    commodity = GetCommodity('act:commodity')
    parent_guid = GetText('act:parent')
    parent = GetAccount('act:parent')
    slots = GetElement('act:slots')

    def _init(self):
        GetAccount.register(self)

    def __repr__(self):
        return f'<Account {self.name}>'

    @property
    def children(self):
        expr = '/gnc-v2/gnc:book/gnc:account/act:parent[text() = $guid]/parent::*'
        return self.xpath(expr, guid=self.guid, namespaces=self.nsmap)

    @property
    def splits(self):
        expr = '/gnc-v2/gnc:book/gnc:transaction/trn:splits/trn:split/split:account[text() = $guid]/parent::*'
        return self.xpath(expr, guid=self.guid, namespaces=self.nsmap)

    @property
    def fullname(self):
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
    """

    guid = GetText('trn:id')
    currency = GetCommodity('trn:currency')
    num = GetText('trn:num')
    date = GetDate('trn:date-posted/ts:date')
    date_entered = GetDate('trn:date-entered/ts:date')
    description = GetText('trn:description')
    splits = GetElement('trn:splits')
    slots = GetElement('trn:slots')

    def __repr__(self):
        return f"<Transaction on {self.date} {self.description}>"


@trn_element('split')
class Split(etree.ElementBase):
    """
    A split is one entry in a transaction.
    <trn:split/>
    """

    guid = GetText('split:id')
    memo = GetText('split:memo')
    reconciled_state = GetText('split:reconciled-state')
    reconcile_date = GetDate('split:reconcile-date/ts:date')
    value = GetNumber('split:value')
    quantity = GetNumber('split:quantity')
    account = GetAccount('split:account')
    action = GetText('split:action')
    slots = GetElement('split:slots')

    @property
    def transaction(self):
        return self.getparent().getparent()

    def __repr__(self):
        return f"<Split {self.transaction.date} '{self.account}' {self.value}>"


@none_element('slot')
class Slot(etree.ElementBase):
    """
    A slot contains all kind of information.
    <slot/>
    """
    key = GetText('slot:key')
    value = GetValue('slot:value')

    def __repr__(self):
        return f"<Slot {self.key}:{self.value}'>"