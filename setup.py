#!/usr/bin/env python

import os
import shutil

from distutils.core import setup

if not os.path.exists("README.txt"):
    shutil.copy("README.md", "README.txt")

setup(name='gnucashxml',
      version='1.9',
      description="Parse GnuCash XML files",
      long_description=open("README.md").read(),
      author="Jorgen Schaefer",
      author_email="forcer@forcix.cx",
      url="https://github.com/jorgenschaefer/gnucashxml",
      py_modules=['gnucashxml'],
      install_requires=[
          'python-dateutil', 'lxml'
      ],
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          ("License :: OSI Approved :: "
           "GNU General Public License v3 or later (GPLv3+)"),
          "Topic :: Office/Business :: Financial :: Accounting",
          ],
      license="GPL",
      )
