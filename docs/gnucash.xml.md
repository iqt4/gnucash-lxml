# GnuCash XML structure:
```
gnc-v2/
├── gnc:count-data
└── gnc:book/
    ├── book:id
    ├── book:slots/
    │   └── slot/
    │       ├── slot:key
    │       └── slot:value
    ├── gnc:commodity/
    │   ├── cmdty:space
    │   ├── cmdty:id
    │   ├── cmdty:name
    │   ├── cmdty:xcode
    │   ├── cmdty:fraction
    │   ├── cmdty:get_quotes
    │   ├── cmdty:quote_sources
    │   ├── cmdty:quote_tz
    │   └── cmdty:slots
    ├── gnc:pricedb/
    │   └── price/
    │       ├── price:id
    │       ├── price:commodity
    │       ├── price:currency
    │       ├── price:time
    │       ├── price:source
    │       ├── price:type
    │       └── price:value
    ├── gnc:account/
    │   ├── act:name
    │   ├── act:id
    │   ├── act:type
    │   ├── act:commodity
    │   ├── act:commodity-scu
    │   ├── act:non-standard-scu
    │   ├── act:code
    │   ├── act:description
    │   ├── act:slots
    │   ├── act:parent
    │   └── act:lots
    └── gnc:transaction/
        ├── trn:id
        ├── trn:num
        ├── trn:currency
        ├── trn:date-posted
        ├── trn:date-entered
        ├── trn:description
        ├── trn:slots
        └── trn:splits/
            └── trn:split/
                ├── split:id
                ├── split:memo
                ├── split:action
                ├── split:reconciled-state
                ├── split:reconcile-date
                ├── split:value
                ├── split:quantity
                ├── split:account
                ├── split:slots
                └── split:lot
```
# Main components:
| Component         | Description                                 |
|-------------------|---------------------------------------------|
| Book              | Root container                              |
| Commodities       | Define currencies and securities            |
| Price database    | Tracks historical prices                    |
| Accounts          | Form a hierarchical structure               |
| Transactions      | Contain splits that link to accounts        |

Each element type has its own namespace which matches the Python class structure in model.py as follows:
| XML Element         | Python Class |
|---------------------|--------------|
| gnc:book            | Book         |
| gnc:commodity       | Commodity    |
| gnc:pricedb         | Book.prices  |
| gnc:account         | Account      |
| gnc:transaction     | Transaction  |
| trn:split           | Split        |

# Source
[commodity ids](https://github.com/Gnucash/gnucash/blob/035819323fd9c344260521ddcbfe640204159732/libgnucash/backend/xml/gnc-commodity-xml-v2.cpp#L46)
[account ids](https://github.com/Gnucash/gnucash/blob/035819323fd9c344260521ddcbfe640204159732/libgnucash/backend/xml/gnc-account-xml-v2.cpp#L51)
[trn_dom_handlers](https://github.com/Gnucash/gnucash/blob/035819323fd9c344260521ddcbfe640204159732/libgnucash/backend/xml/gnc-transaction-xml-v2.cpp#L545)
[spl_dom_handlers](https://github.com/Gnucash/gnucash/blob/035819323fd9c344260521ddcbfe640204159732/libgnucash/backend/xml/gnc-transaction-xml-v2.cpp#L354)
<!-- Contains AI-generated edits. -->