# GnuCash XML Library

`gnucashxml` is a pure [Python][] library to parse [GnuCash][] XML files.
This allows writing reporting utilities that do not rely on the GnuCash
libraries themselves, or require the main program to run at all.

Coding is based on the work from other authors (see copyright).
The library supports extracting the account tree, including all
prices, transactions and splits. It does not support scheduled 
transactions, and likely none but the most basic commodities. In 
particular, writing of XML files is not supported.

**Testing with GnuCash 4.x is ongoing.**

[python]: http://www.python.org/
[gnucash]: http://www.gnucash.org/

## Usage

The interface is intended to allow quickly writing reports or extract data
using Python. The extractor is based on the [lxml][] library and the core
elements are [custom Element classes in lxml][]. Thus, all functions from the
library can be used. **Warning**: The API of this interface is not always 
compatible with previous versions!

Dates or times are represented by the standard library `datetime`. All account
and transaction balances are represented as the standard `Decimal` type.


The three main concepts in GnuCash are accounts, transactions, and
splits. A transaction consists of a number of splits that specify from
which account or to which account commodities are transferred by this
transaction. All splits within a transaction together are balanced.

The main classes provided by `gnucashxml` mirror these concepts. A
`Book` is the main class containing everything else. A `Commodity` is
what is stored in an account, for example, Euros or Dollars. An
`Account` is part of a tree structure and contains splits. `Splits`
again are part of `Transactions`.

These classes may have `Slot` members, which is a hierarchy of `key`
and `value` for extra information. GnCash information such as "hidden" are
recorded here.

It allows you to:
- open existing GnuCash documents and access accounts, transactions, splits and slots

[lxml]: https://lxml.de
[custom element classes in lxml]: https://lxml.de/element_classes.html
## Example

```Python
import gnucashxml

book = gnucashxml.load("test.gnucash")

income_total = 0
expense_total = 0
for account, subaccounts, splits in book.walk():
    if account.actype == 'INCOME':
        income_total += sum(split.value for split in account.splits)
    elif account.actype == 'EXPENSE':
        expense_total += sum(split.value for split in account.splits)

print("Total income : {:9.2f}".format(income_total * -1))
print("Total expense: {:9.2f}".format(expense_total))
```

Print list of account names:
```Python
import gnucashxml

book = gnucashxml.load("test.gnucash")
for act in book.accounts:
    print(act.fullname)
```
