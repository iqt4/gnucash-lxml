#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# inspired by https://blog.ionelmc.ro/2014/05/25/python-packaging/
#
import io

from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
            join(dirname(__file__), *names),
            encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


setup(
    name='gnucashxml',
    version='1.x',
    description="Parse GnuCash XML files",
    long_description=read("README.md"),
    author="Dirk Silkenbäumer",
    author_email="none",
    url="https://github.com/iqt4/gnucashxml",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    install_requires=[
        'python-dateutil', 'lxml',
    ],
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        ("License :: OSI Approved :: "
         "GNU General Public License v3 or later (GPLv3+)"),
        "Programming Language :: Python",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    license="GPL",
)
