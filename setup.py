"""
Setup for pyparrot_windows, a fork of pyparrot adding Windows/macOS BLE support.

Original pyparrot by Dr. Amy McGovern (MIT License):
    https://github.com/amymcgovern/pyparrot
This fork:
    https://github.com/DAUST-CRAS/pyparrot_windows

The package still installs and imports as `pyparrot` so all existing
pyparrot code and tutorials keep working:
    from pyparrot.Minidrone import Mambo

NOTE: this fork is installed from GitHub, not PyPI:
    pip install git+https://github.com/DAUST-CRAS/pyparrot_windows.git
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    # Keep the import/package name 'pyparrot' so user code is unchanged.
    # Do NOT upload this fork to PyPI under this name -- install from GitHub.
    name='pyparrot',

    # Fork versioning: 2.x = the bleak-based cross-platform BLE line.
    # (Upstream stopped at 1.5.21.)
    version='2.0.0',

    description='Python interface to control Parrot drones '
                '(fork with Windows/macOS BLE support via bleak)',

    long_description=long_description,
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',

    url='https://github.com/DAUST-CRAS/pyparrot_windows',

    # Original author -- keep for attribution (MIT License)
    author='Amy McGovern',
    author_email='dramymcgovern@gmail.com',

    # Fork maintainer
    maintainer='DAUST-CRAS',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Topic :: Education',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
    ],

    keywords='python parrot drone education programming mambo bluetooth ble windows',

    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'coursework']),
    include_package_data=True,

    # Dependencies. All pinned to the exact versions verified with real
    # Mambo flights (Windows 11, Python 3.14, July 2026). Re-run a full
    # takeoff/land test before loosening any pin.
    #
    # - bleak: BLE library. Changed its notification-callback API before
    #   (0.19), so upgrades are risky without a flight test.
    # - untangle: XML parser for the drone command files. Its handling of
    #   the reserved element name <class> changed across versions; our XML
    #   files use <myclass> (matching pyparrot's code), which parses
    #   identically on every untangle version, but we pin for repeatability.
    # - zeroconf: only used by the WiFi connection, but Minidrone.py imports
    #   it unconditionally, so it's required even for BLE-only use.
    install_requires=[
        'untangle==1.2.1',
        'bleak==3.0.2',
        'zeroconf==0.150.0',
    ],

    # bleak requires modern Python; 3.9+ keeps us comfortably compatible.
    python_requires='>=3.9',

    # After `pip install`, students can type `find_mambo` in any terminal
    # to scan for drone addresses. Points at the bleak-based scanner
    # (the old bluepy one has been replaced -- see pyparrot/scripts/findMambo.py).
    entry_points={
        'console_scripts': [
            'find_mambo=pyparrot.scripts.findMambo:main',
        ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/DAUST-CRAS/pyparrot_windows/issues',
        'Source': 'https://github.com/DAUST-CRAS/pyparrot_windows',
        'Original pyparrot': 'https://github.com/amymcgovern/pyparrot',
        'Original Documentation': 'https://pyparrot.readthedocs.io',
    },
)
