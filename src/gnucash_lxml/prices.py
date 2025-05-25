import uuid
from lxml import etree
from .query import GetText, GetDate, GetNumber
from .model import gnc_element, none_element, UnsupportedVersionError

@gnc_element('pricedb')
class PriceDB(etree.ElementBase):
    """
    A price database containing historical prices for commodities.
    <gnc:pricedb/>

    XML Structure:
        price -> prices (list[Price]): List of price entries
    """
    SUPPORTED_VERSIONS = ['1']

    def _init(self):
        """Initialize price database and verify version"""
        version = self.get('version', None)
        if version not in self.SUPPORTED_VERSIONS:
            raise UnsupportedVersionError(
                f"PriceDB version '{version}' not supported. Supported version: {self.SUPPORTED_VERSIONS}"
            )
        self._prices = None

    def __repr__(self):
        return f"<PriceDB with {len(self.prices)} entries>"

    @property
    def prices(self):
        """
        Price entries with lazy loading.
        Returns list of Price objects.
        """
        if self._prices is None:
            self._prices = self.findall('price', namespaces=self.nsmap)
        return self._prices or []


@none_element('price')
class Price(etree.ElementBase):
    """
    A price represents the value of a commodity in terms of a currency at a specific date.
    <price/>

    XML Structure:
        price:id         -> guid (str): Unique identifier
        price:commodity  -> commodity (Commodity): The commodity being priced
        price:currency   -> currency (Commodity): The currency used for pricing
        price:time       -> date (datetime): Date of the price quote
        price:value      -> value (Decimal): The price value
    
    Not Implemented:
        - price:type:    Optional price type
        - price:source:  Optional source of price data
    """
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

# Contains AI-generated edits.
