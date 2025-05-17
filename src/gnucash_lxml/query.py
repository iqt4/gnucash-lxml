# query.py --- Query descriptor classes for GnuCash XML
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

import decimal
from abc import ABC, abstractmethod
from dateutil.parser import parse as parse_date
from lxml import etree
from typing import Any

class QueryBase(ABC):
    """Base class for XML element query descriptors"""
    def __get__(self, obj: etree.ElementBase, obj_type=None) -> Any:
        return self.query_function(obj)
    
    @abstractmethod
    def query_function(self, obj: etree.ElementBase) -> Any:
        """Execute the query on the element"""
        ...


class GetElement(QueryBase):
    """Query descriptor to retrieve an XML element by path"""
    def __init__(self, path: str):
        self.path = path

    def query_function(self, obj: etree.ElementBase) -> etree.ElementBase:
        return obj.find(self.path, namespaces=obj.nsmap)


class GetText(QueryBase):
    """Query descriptor to retrieve text content of an XML element by path"""
    def __init__(self, path: str):
        self.path = path

    def query_function(self, obj: etree.ElementBase) -> str:
        return obj.findtext(self.path, default=None, namespaces=obj.nsmap)

class GetDate(QueryBase):
    """Query descriptor to retrieve a date from an XML element by path"""
    def __init__(self, path: str):
        self.path = path

    def query_function(self, obj: etree.ElementBase) -> Any:
        date_str = obj.findtext(self.path, default=None, namespaces=obj.nsmap)
        if date_str is not None:
            return parse_date(date_str)


class GetNumber(QueryBase):
    """Query descriptor to retrieve a number from an XML element by path"""
    def __init__(self, path: str):
        self.path = path

    def query_function(self, obj: etree.ElementBase) -> decimal.Decimal:
        number_str = obj.findtext(self.path, default=None,namespaces=obj.nsmap)
        numerator, denominator = number_str.split("/")
        return decimal.Decimal(numerator) / decimal.Decimal(denominator)

class GetValue(QueryBase):
    """Query descriptor to retrieve a value from an XML element by path"""
    def __init__(self, path: str):
        self.path = path

    def value_lookup(self, e: etree.ElementBase) -> Any:
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
            return parse_date(e.findtext("gdate", default=None, namespaces=e.nsmap))
        elif value_type == 'timespec':
            return parse_date(e.findtext('ts:date', default=None, namespaces=e.nsmap))
        elif value_type == 'frame':
            return list(e) # type: ignore 
        elif value_type == 'list':
            return [self.value_lookup(list_e) for list_e in e] # type: ignore
        else:
            raise RuntimeError(f"Unknown slot type {value_type}")

    def query_function(self, obj: etree.ElementBase) -> Any:
        e: etree.ElementBase = obj.find(self.path, obj.nsmap)
        return self.value_lookup(e)


class GetCommodity(QueryBase):
    """
    Query descriptor to retrieve a Commodity instance from an XML element by path
    """
    # Map between tuple of space.symbol and Commodity instance
    _commodity_index = {}

    def __init__(self, path: str):
        self.path = path
    def query_function(self, obj: etree.ElementBase) -> Any:
        e = obj.find(self.path, obj.nsmap)
        if e is not None:
            c_space = e.findtext('cmdty:space', namespaces=e.nsmap)
            c_symbol = e.findtext('cmdty:id', namespaces=e.nsmap)
            return self._commodity_index.get((c_space, c_symbol))

    @classmethod
    def register(cls, obj: Any):
        cls._commodity_index.setdefault((obj.space, obj.symbol), obj)


class GetAccount(QueryBase):
    """
    Query descriptor to retrieve an Account instance by GUID
    """
    # Map between GUID and Account instance
    _account_index = {}

    def __init__(self, path: str):
        self.path = path
    def query_function(self, obj: Any) -> Any:
        e: etree.ElementBase = obj.find(self.path, obj.nsmap)
        if e is not None and e.get("type", None) == "guid":
            return self._account_index.get(e.text)

    @classmethod
    def register(cls, obj: Any):
        cls._account_index.setdefault(obj.guid, obj)

# Contains AI-generated edits.