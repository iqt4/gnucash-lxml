# parsing.py --- XML parsing utilities for GnuCash XML files
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

from lxml import etree
from .models import Book, Commodity, Account, Transaction, Price, Split, Slot, ns_lookup

def load(source) -> Book:
    """
    Load GnuCash XML from <source> and return Book.
    """
    # Not implemented:
    # - gnc:count-data

    parser = etree.XMLParser()
    parser.set_element_class_lookup(ns_lookup)
    root = etree.parse(source, parser=parser).getroot()
    return root.find('gnc:book', root.nsmap)

# Contains AI-generated edits.
