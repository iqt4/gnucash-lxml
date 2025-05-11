# gnucashxml-lxml package --- Parse GNU Cash XML files
# Copyright (C) 2012 Jorgen Schaefer <forcer@forcix.cx>
#           (C) 2017 Christopher Lam
#           (C) 2025 Dirk Silkenbäumer
# SPDX-License-Identifier: GPL-3.0-or-later

from .parsing import load
from .models import Book, Commodity, Price, Account, Transaction, Split, Slot

__version__ = "1.90"

# Contains AI-generated edits.
