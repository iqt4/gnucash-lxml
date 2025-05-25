# query.py --- Query descriptor classes for GnuCash XML
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

import decimal
from abc import ABC, abstractmethod
from datetime import datetime
from dateutil.parser import parse as parse_date
from lxml import etree
from typing import Any, Optional

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

    def query_function(self, obj: etree.ElementBase) -> Optional[datetime]:
        date_str = obj.findtext(self.path, default=None, namespaces=obj.nsmap)
        if date_str is not None:
            return parse_date(date_str)
        return None

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
