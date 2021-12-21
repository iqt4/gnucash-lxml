# gnucashxml.py --- Parse GNU Cash XML files

# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam

# Author: Jorgen Schaefer <forcer@forcix.cx>
#         Christopher Lam <https://github.com/christopherlam>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations
from abc import ABC, abstractmethod
import decimal
from dateutil.parser import parse as parse_date
from lxml import etree

__version__ = "1.90"


def load(source):
    """
    Load GnuCash XML from <source> and return Book.

    The ``source`` can be any of the following:
    - a file name/path
    - a file object
    - a file-like object
    - a URL using the HTTP or FTP protocol
    <gnc:book/>
    """
    # Not implemented:
    # - gnc:count-data

    parser = get_xml_parser()
    root = etree.parse(source, parser=parser).getroot()
    return root.find('gnc:book', root.nsmap)


def get_xml_parser():
    lookup = etree.ElementNamespaceClassLookup()
    gnc_element = lookup.get_namespace('http://www.gnucash.org/XML/gnc')
    gnc_element['book'] = Book
    gnc_element['commodity'] = Commodity
    gnc_element['account'] = Account
    gnc_element['transaction'] = Transaction
    gnc_element['price'] = Price
    trn_element = lookup.get_namespace('http://www.gnucash.org/XML/trn')
    trn_element['split'] = Split
    no_namespace = lookup.get_namespace(None)
    no_namespace['slot'] = Slot

    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    return parser


class SlotElementLookup(etree.CustomElementClassLookup):
    def lookup(self, node_type, document, namespace, name):
        if node_type == 'element' and namespace is None and name == 'slot':
            return Slot
        else:
            return None  # pass on to (default) fallback


class QueryBase(ABC):
    def __get__(self, obj, obj_type=None):
        return self.query_function(obj)

    @abstractmethod
    def query_function(self, obj):
        pass


class GetElement(QueryBase):
    def __init__(self, path):
        self.path = path

    def query_function(self, element: etree.ElementBase):
        return element.find(self.path, namespaces=element.nsmap)


class GetText(QueryBase):
    def __init__(self, path):
        self.path = path

    def query_function(self, element: etree.ElementBase):
        return element.findtext(self.path, namespaces=element.nsmap)


class GetDate(QueryBase):
    def __init__(self, path):
        self.path = path

    def query_function(self, element: etree.ElementBase):
        date_str = element.findtext(self.path, namespaces=element.nsmap)
        if date_str is not None:
            return parse_date(date_str)


class GetNumber(QueryBase):
    def __init__(self, path):
        self.path = path

    def query_function(self, element: etree.ElementBase):
        number_str = element.findtext(self.path, namespaces=element.nsmap)
        numerator, denominator = number_str.split("/")
        return decimal.Decimal(numerator) / decimal.Decimal(denominator)


class GetValue(QueryBase):
    def __init__(self, path):
        self.path = path

    def value_lookup(self, e: etree.ElementBase):
        value_str = e.text
        value_type = e.get('type', default='string')
        if value_type in ('integer', 'double'):
            return int(value_str)
        elif value_type == 'numeric':
            numerator, denominator = value_str.split("/")
            return decimal.Decimal(numerator) / decimal.Decimal(denominator)
        elif value_type in ('string', 'guid'):
            return value_str
        elif value_type == 'gdate':
            return parse_date(e.findtext("gdate"))
        elif value_type == 'timespec':
            return parse_date(e.findtext('ts:date'))
        elif value_type == 'frame':
            return list(e)
        elif value_type == 'list':
            return [self.value_lookup(list_e) for list_e in e]
        else:
            raise RuntimeError(f"Unknown slot type {value_type}")

    def query_function(self, element: etree.ElementBase):
        e: etree.ElementBase = element.find(self.path, element.nsmap)
        return self.value_lookup(e)


class GetCommodity(QueryBase):
    """
    Return Commodity instance from path to
    """
    # Map between tuple of space.symbol and Commodity instance
    _commodity_index = {}

    def __init__(self, path):
        self.path = path

    def query_function(self, element: etree.ElementBase):
        e = element.find(self.path, element.nsmap)
        if e is not None:
            c_space = e.findtext('cmdty:space', namespaces=e.nsmap)
            c_symbol = e.findtext('cmdty:id', namespaces=e.nsmap)
            return self._commodity_index.get((c_space, c_symbol))

    @classmethod
    def register(cls, obj):
        cls._commodity_index.setdefault((obj.space, obj.symbol), obj)


class GetAccount(QueryBase):
    """
    Return Account instance by GUID
    """
    # Map between GUID and Account instance
    _account_index = {}

    def __init__(self, path):
        self.path = path

    def query_function(self, act: Account):
        e: etree.ElementBase = act.find(self.path, act.nsmap)
        if e is not None and e.get("type") == "guid":
            # xpath is slow
            # expr = '/gnc-v2/gnc:book/gnc:account/act:id[text() = $guid]/parent::*'
            # return e.xpath(expr, guid=e.text, namespaces=e.nsmap)[0]
            return self._account_index.get(e.text)

    @classmethod
    def register(cls, obj):
        cls._account_index.setdefault(obj.guid, obj)


class Book(etree.ElementBase):
    """
    A book is the main container for GNU Cash data.

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
        self.findall('gnc:commodity', self.nsmap)  # Initialize the Commodity classes
        self.findall('gnc:account', self.nsmap)  # Initialize the Account classes

    def __repr__(self):
        return f"<Book {self.guid}>"

    @property
    def commodities(self):
        return self.iterfind('gnc:commodity', self.nsmap)

    @property
    def root_account(self):
        return self.accounts[0]

    @property
    def accounts(self):
        return list(self.iterfind('gnc:account', self.nsmap))

    @property
    def transactions(self):
        return self.iterfind('gnc:transaction', self.nsmap)

    def walk(self):
        return self.root_account.walk()

#     def find_account(self, name):
#         for account, children, splits in self.walk():
#             if account.name == name:
#                 return account
#
#     def find_guid(self, guid):
#         for item in self.accounts + self.transactions:
#             if item.guid == guid:
#                 return item


class Commodity(etree.ElementBase):
    """
    A commodity is something that's stored in GNU Cash accounts.
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


class Price(etree.ElementBase):
    """
    A price is GnuCash record of the price of a commodity against a currency
    Consists of date, currency, commodity,  value
    <gnc:pricedb/>
    """

    guid = GetText('price:id')
    commodity = GetCommodity('price:commodity')
    currency = GetCommodity('price:currency)')
    date = GetDate('price:time/ts:date')
    value = GetNumber('price:value')

    def __repr__(self):
        return f"<Price {self.date:%Y/%m/%d}: {self.value} {self.commodity}/{self.currency} >"


#    def __lt__(self, other):
#        # For sorted() only
#        if isinstance(other, Price):
#            return self.date < other.date
#        else:
#            False


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
    #
    # def find_account(self, name):
    #     for account, children, splits in self.walk():
    #         if account.name == name:
    #             return account
    #
    # def get_all_splits(self):
    #     split_list = []
    #     for account, children, splits in self.walk():
    #         split_list.extend(splits)
    #     return sorted(split_list)
    #
    # def __lt__(self, other):
    #     # For sorted() only
    #     if isinstance(other, Account):
    #         return self.fullname() < other.fullname()
    #     else:
    #         False


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


#     def __lt__(self, other):
#         # For sorted() only
#         if isinstance(other, Transaction):
#             return self.date < other.date
#         else:
#             False


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


#     def __lt__(self, other):
#         # For sorted() only
#         if isinstance(other, Split):
#             return self.transaction < other.transaction
#         else:
#             False


class Slot(etree.ElementBase):
    """
    A slot contains all kind of information.
    <slot/>
    """
    key = GetText('slot:key')
    value = GetValue('slot:value')

    def __repr__(self):
        return f"<Slot {self.key}:{self.value}'>"


if __name__ == "__main__":
    book = load("../Haushalt.gnucash.gz")

    for act in book.accounts:
        print(act.fullname)
