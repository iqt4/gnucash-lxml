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

import decimal
import gzip
from dateutil.parser import parse as parse_date

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

__version__ = "1.1"


class CallableList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def __call__(self, **kwargs):
        """
        Return the first element of the list that has attributes matching the kwargs dict.
        To be used as::
            l(mnemonic="EUR", namespace="CURRENCY")
        """
        for obj in self:
            for k, v in kwargs.items():
                if getattr(obj, k) != v:
                    break
            else:
                return obj
        else:
            return None


class Book(object):
    """
    A book is the main container for GNU Cash data.

    It doesn't really do anything at all by itself, except to have
    a reference to the accounts, transactions, prices, and commodities.
    """

    def __init__(self, tree, guid, prices=None, transactions=None, root_account=None,
                 accounts=None, commodities=None, slots=None):
        self.tree = tree
        self.guid = guid
        self.prices = prices
        self.transactions = transactions or []
        self.root_account = root_account
        self.accounts = accounts or []
        self.commodities = commodities or []
        self.slots = slots or {}

    def __repr__(self):
        return "<Book {}>".format(self.guid)

    def walk(self):
        return self.root_account.walk()

    def find_account(self, name):
        for account, children, splits in self.walk():
            if account.name == name:
                return account

    def find_guid(self, guid):
        for item in self.accounts + self.transactions:
            if item.guid == guid:
                return item

    def ledger(self):
        outp = []

        for comm in self.commodities:
            outp.append('commodity {}'.format(comm.name))
            outp.append('\tnamespace {}'.format(comm.space))
            outp.append('')

        for account in self.accounts:
            outp.append('account {}'.format(account.fullname()))
            if account.description:
                outp.append('\tnote {}'.format(account.description))
            outp.append('\tcheck commodity == "{}"'.format(account.commodity))
            outp.append('')

        for trn in sorted(self.transactions):
            outp.append('{:%Y/%m/%d} * {}'.format(trn.date, trn.description))
            for spl in trn.splits:
                outp.append('\t{:50} {:12.2f} {} {}'.format(spl.account.fullname(),
                                                            spl.value,
                                                            spl.account.commodity,
                                                            '; ' + spl.memo if spl.memo else ''))
            outp.append('')

        return '\n'.join(outp)


class Commodity(object):
    """
    A commodity is something that's stored in GNU Cash accounts.

    Consists of a name (or id) and a space (namespace).
    """

    # Not implemented
    # - fraction
    # - slots
    def __init__(self, space, symbol, name=None, xcode=None):
        self.space = space
        self.symbol = symbol
        self.name = name
        self.xcode = xcode

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Commodity {}:{}>".format(self.space, self.symbol)

    # for compatibility with piecash
    @property
    def cusip(self):
        return self.xcode

    @property
    def fullname(self):
        return self.name

    @property
    def mnemonic(self):
        return self.symbol


class Account(object):
    """
    An account is part of a tree structure of accounts and contains splits.
    """

    def __init__(self, name, guid, actype, parent=None,
                 commodity=None, commodity_scu=None,
                 description=None, slots=None):
        self.name = name
        self.guid = guid
        self.actype = actype
        self.description = description
        self.parent = parent
        self.children = []
        self.commodity = commodity
        self.commodity_scu = commodity_scu
        self.splits = []
        self.slots = slots or {}

    @property
    def fullname(self):
        if self.parent:
            pfn = self.parent.fullname
            if pfn:
                return '{}:{}'.format(pfn, self.name)
            else:
                return self.name
        else:
            return ''

    def __repr__(self):
        return "<Account '{}[{}]' {}...>".format(self.name, self.commodity.symbol, self.guid[:10])

    def walk(self):
        """
        Generate splits in this account tree by walking the tree.

        For each account, it yields a 3-tuple (account, subaccounts, splits).

        You can modify the list of subaccounts, but should not modify
        the list of splits.
        """
        accounts = [self]
        while accounts:
            acc, accounts = accounts[0], accounts[1:]
            children = list(acc.children)
            yield acc, children, acc.splits
            accounts.extend(children)

    def find_account(self, name):
        for account, children, splits in self.walk():
            if account.name == name:
                return account

    def get_all_splits(self):
        split_list = []
        for account, children, splits in self.walk():
            split_list.extend(splits)
        return sorted(split_list)

    def __lt__(self, other):
        # For sorted() only
        if isinstance(other, Account):
            return self.fullname() < other.fullname()
        else:
            False


class Transaction(object):
    """
    A transaction is a balanced group of splits.
    """

    def __init__(self, guid=None, currency=None,
                 date=None, date_entered=None,
                 description=None, splits=None,
                 num=None, slots=None):
        self.guid = guid
        self.currency = currency
        self.date = date
        self.date_entered = date_entered
        self.description = description
        self.num = num or None
        self.splits = splits or []
        self.slots = slots or {}

    def __repr__(self):
        return "<Transaction on {} '{}' {}...>".format(
            self.date, self.description, self.guid[:6])

    def __lt__(self, other):
        # For sorted() only
        if isinstance(other, Transaction):
            return self.date < other.date
        else:
            False

    # for compatibility with piecash
    @property
    def post_date(self):
        return self.date


class Split(object):
    """
    A split is one entry in a transaction.
    """

    def __init__(self, guid=None, memo=None,
                 reconciled_state=None, reconcile_date=None, value=None,
                 quantity=None, account=None, transaction=None, action=None,
                 slots=None):
        self.guid = guid
        self.reconciled_state = reconciled_state
        self.reconcile_date = reconcile_date
        self.value = value
        self.quantity = quantity
        self.account = account
        self.transaction = transaction
        self.action = action
        self.memo = memo
        self.slots = slots

    def __repr__(self):
        return "<Split {}: {} {}...>".format(
            self.account, self.value, self.guid[:6])

    def __lt__(self, other):
        # For sorted() only
        if isinstance(other, Split):
            return self.transaction < other.transaction
        else:
            False


class Price(object):
    """
    A price is GNUCASH record of the price of a commodity against a currency
    Consists of date, currency, commodity,  value
    """

    def __init__(self, guid=None, commodity=None, currency=None,
                 date=None, value=None):
        self.guid = guid
        self.commodity = commodity
        self.currency = currency
        self.date = date
        self.value = value

    def __repr__(self):
        return "<Price {}... {:%Y/%m/%d}: {} {}/{} >".format(self.guid[:6],
                                                             self.date,
                                                             self.value,
                                                             self.commodity,
                                                             self.currency)

    def __lt__(self, other):
        # For sorted() only
        if isinstance(other, Price):
            return self.date < other.date
        else:
            False


##################################################################
# XML file parsing

def from_filename(filename):
    """Parse a GNU Cash file and return a Book object."""
    try:
        # try opening with gzip decompression
        return _iterparse(gzip.open(filename, "rb"))
    except IOError:
        # try opening without decompression
        return _iterparse(open(filename, "rb"))


def _parse_number(numstring):
    num, denum = numstring.split("/")
    return decimal.Decimal(num) / decimal.Decimal(denum)


# Implemented:
# - gnc:count-data
# - gnc:book
# - book:id
# - gnc:commodity
# - gnc:account
# - gnc:transaction

# Not implemented:
# - book:slots
# - gnc:pricedb
# - gnc:schedxaction
# - gnc:template-transactions
def _iterparse(fobj):

    def _add_guid(elem):
        book.guid = elem.text

    # Implemented:
    # - cmdty:space
    # - cmdty:id => Symbol
    # - cmdty:name
    # - cmdty:xcode => optional, e.g. ISIN/WKN
    #
    # Not implemented:
    # - cmdty:get_quotes => unknown, empty, optional
    # - cmdty:quote_tz => unknown, empty, optional
    # - cmdty:source => text, optional, e.g. "currency"
    # - cmdty:fraction => optional, e.g. "1"
    def _add_commodity(cmdty_tree):
        c_space = cmdty_tree.find('./cmdty:space', ns).text
        c_id = cmdty_tree.find('./cmdty:id', ns).text
        commodity = Commodity(c_space, c_id)
        try:
            commodity.name = cmdty_tree.find('./cmdty:name', ns).text
        except AttributeError:
            pass

        try:
            commodity.xcode = cmdty_tree.find('./cmdty:xcode', ns).text
        except AttributeError:
            pass

        cmdty_dict[(c_space, c_id)] = commodity
        book.commodities.append(commodity)

    # Implemented:
    # - act:name
    # - act:id
    # - act:type
    # - act:description
    # - act:commodity
    # - act:commodity-scu
    # - act:parent

    # Not implemented
    # - act:slots
    def _add_account(a_tree):
        act_name = a_tree.find('./act:name', ns).text
        act_id = a_tree.find('./act:id', ns).text
        act_type = a_tree.find('./act:type', ns).text

        account = Account(act_name, act_id, act_type)

        if act_type != 'ROOT':
            c_space = a_tree.find('./act:commodity/cmdty:space', ns).text
            c_id = a_tree.find('./act:commodity/cmdty:id', ns).text
            account.commodity = cmdty_dict[(c_space, c_id)]

            account.commodity_scu = a_tree.find('./act:commodity-scu', ns).text
            description = a_tree.find('./act:description', ns)
            if description is not None:
                account.description = description.text
            parent_id = a_tree.find('./act:parent', ns).text
            acc_parent = act_dict[parent_id]
            account.parent = acc_parent
            acc_parent.children.append(account)

        act_dict[act_id] = account
        book.accounts.append(account)

    # Implemented:
    # - split:id
    # - split:memo
    # - split:reconciled-state
    # - split:reconcile-date
    # - split:value
    # - split:quantity
    # - split:account
    # - split:action

    # Not implemented:
    # - split:slots
    def _get_split_from_trn(split_tree, transaction):
        guid = split_tree.find('./split:id', ns).text
        memo = split_tree.find('./split:memo', ns)
        if memo is not None:
            memo = memo.text
        reconciled_state = split_tree.find('./split:reconciled-state', ns).text
        reconcile_date = split_tree.find('./split:reconcile-date/ts:date', ns)
        if reconcile_date is not None:
            reconcile_date = parse_date(reconcile_date.text)
        value = _parse_number(split_tree.find('./split:value', ns).text)
        quantity = _parse_number(split_tree.find('./split:quantity', ns).text)
        account_guid = split_tree.find('./split:account', ns).text
        account = act_dict[account_guid]
        # slots = _slots_from_tree(split_tree.find(split + "slots"))
        action = split_tree.find('./split:action', ns)
        if action is not None:
            action = action.text

        split = Split(guid=guid,
                      memo=memo,
                      reconciled_state=reconciled_state,
                      reconcile_date=reconcile_date,
                      value=value,
                      quantity=quantity,
                      account=account,
                      transaction=transaction,
                      action=action)

        account.splits.append(split)
        return split

    # Implemented:
    # - trn:id
    # - trn:currency
    # - trn:date-posted
    # - trn:date-entered
    # - trn:description
    # - trn:splits / trn:split

    # Not implemented:
    # - trn:slots
    def _add_transaction(trn_tree):
        guid = trn_tree.find('./trn:id', ns).text
        c_space = trn_tree.find('./trn:currency/cmdty:space', ns).text
        c_symbol = trn_tree.find('./trn:currency/cmdty:id', ns).text
        currency = cmdty_dict[(c_space, c_symbol)]
        date_posted = parse_date(trn_tree.find('./trn:date-posted/ts:date', ns).text)
        date_entered = parse_date(trn_tree.find('./trn:date-entered/ts:date', ns).text)
        description = trn_tree.find('./trn:description', ns).text

        # slots = _slots_from_tree(tree.find(trn + "slots"))
        transaction = Transaction(guid=guid,
                                  currency=currency,
                                  date=date_posted,
                                  date_entered=date_entered,
                                  description=description)
        book.transactions.append(transaction)

        for split_tree in trn_tree.findall('trn:splits/trn:split', ns):
            split = _get_split_from_trn(split_tree, transaction)
            transaction.splits.append(split)

    def _count_data(elem):
        count_data[elem.get('{http://www.gnucash.org/XML/cd}type')] = int(elem.text)

    tag_function = {
        '{http://www.gnucash.org/XML/book}id': _add_guid,
        '{http://www.gnucash.org/XML/gnc}commodity': _add_commodity,
        '{http://www.gnucash.org/XML/gnc}account': _add_account,
        '{http://www.gnucash.org/XML/gnc}transaction': _add_transaction,
        '{http://www.gnucash.org/XML/gnc}count-data': _count_data
    }

    cmdty_dict = {}
    act_dict = {}
    count_data = {}
    ns = {}
    path = []
    root = None
    book = None

    events = ['start-ns', 'start', 'end']
    context = etree.iterparse(fobj, events=events)

    for event, elem in context:
        if event == 'start':
            path.append(elem.tag)

            if root is None:
                root = elem
                if root.tag != 'gnc-v2':
                    raise ValueError("Not a valid GNU Cash v2 XML file")
            elif len(path) == 2:
                if elem.tag == '{http://www.gnucash.org/XML/gnc}count-data' and elem.text != "1":
                    raise ValueError("Only 1 book per XML file allowed")
                elif elem.tag == '{http://www.gnucash.org/XML/gnc}book':
                    book = Book(tree=None, guid=None)

        elif event == 'end':
            if len(path) == 3:
                # print(path[-1], event, elem.tag)
                try:
                    tag_function[elem.tag](elem)
                except KeyError:
                    pass
                root.clear()

            path.pop()

        else:  # event = 'start-ns'
            prefix, uri = elem
            ns[prefix] = uri

    if count_data['account'] != len(book.accounts):
        raise ValueError("Number of Accounts mismatch")
    if count_data['transaction'] != len(book.transactions):
        raise ValueError("Number of Transactions mismatch")
    # 'template' seems not to be counted
    if count_data['commodity'] != len(book.commodities) - 1:
        raise ValueError("Number of Commodities mismatch")

    return book

# From former code
# Todo PriceDB, Slots
def _book_from_tree(tree):

    # Implemented:
    # - price
    # - price:guid
    # - price:commodity
    # - price:currency
    # - price:date
    # - price:value
    def _price_from_tree(tree):
        price = '{http://www.gnucash.org/XML/price}'
        cmdty = '{http://www.gnucash.org/XML/cmdty}'
        ts = "{http://www.gnucash.org/XML/ts}"

        guid = tree.find(price + 'id').text
        value = _parse_number(tree.find(price + 'value').text)
        date = parse_date(tree.find(price + 'time/' + ts + 'date').text)

        currency_space = tree.find(price + "currency/" + cmdty + "space").text
        currency_id = tree.find(price + "currency/" + cmdty + "id").text
        # pricedb may contain currencies not part of the commodities root list
        currency = commoditydict.setdefault((currency_space, currency_id),
                                            Commodity(space=currency_space, id=currency_id))

        commodity_space = tree.find(price + "commodity/" + cmdty + "space").text
        commodity_id = tree.find(price + "commodity/" + cmdty + "id").text
        commodity = commoditydict[(commodity_space, commodity_id)]

        return Price(guid=guid,
                     commodity=commodity,
                     date=date,
                     value=value,
                     currency=currency)

    prices = []
    t = tree.find('{http://www.gnucash.org/XML/gnc}pricedb')
    if t is not None:
        for child in t.findall('price'):
            price = _price_from_tree(child)
            prices.append(price)


# Implemented:
# - slot
# - slot:key
# - slot:value
# - ts:date
# - gdate
# - list
def _slots_from_tree(tree):
    if tree is None:
        return {}
    slot = "{http://www.gnucash.org/XML/slot}"
    ts = "{http://www.gnucash.org/XML/ts}"
    slots = {}
    for elt in tree.findall("slot"):
        key = elt.find(slot + "key").text
        value = elt.find(slot + "value")
        type_ = value.get('type', 'string')
        if type_ in ('integer', 'double'):
            slots[key] = int(value.text)
        elif type_ == 'numeric':
            slots[key] = _parse_number(value.text)
        elif type_ in ('string', 'guid'):
            slots[key] = value.text
        elif type_ == 'gdate':
            slots[key] = parse_date(value.find("gdate").text)
        elif type_ == 'timespec':
            slots[key] = parse_date(value.find(ts + "date").text)
        elif type_ == 'frame':
            slots[key] = _slots_from_tree(value)
        elif type_ == 'list':
            slots[key] = [_slots_from_tree(lelt) for lelt in value.findall(slot + "value")]
        else:
            raise RuntimeError("Unknown slot type {}".format(type_))
    return slots


