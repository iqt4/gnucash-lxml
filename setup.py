from setuptools import setup, find_packages
import io
from os.path import dirname, join

VERSION = "0.1.0a1"

def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()

setup(
    name='gnucash-lxml',
    version=VERSION,
    description="Parse GnuCash XML files",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Dirk Silkenbäumer",
    url="https://github.com/iqt4/gnucash-lxml",
    
    # Package structure
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    
    # Dependencies
    python_requires=">=3.8",
    install_requires=[
        'lxml>=5.0.0',
        'python-dateutil>=2.8.0',
    ],
    extras_require={
        'test': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
        ],
    },
    
    # Metadata
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    license="GPL",
    keywords="gnucash xml finance accounting",
)