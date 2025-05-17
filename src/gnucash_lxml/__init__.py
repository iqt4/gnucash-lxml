# gnucash-lxml package --- Parse GNU Cash XML files
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

from .parsing import load
from .model import Book, Commodity, Price, Account, Transaction, Split, Slot
from importlib.metadata import version

__version__ = version("gnucash-lxml")

# Contains AI-generated edits.
