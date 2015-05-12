# coding=utf-8
from distutils.util import convert_path
import os
from fnmatch import fnmatchcase
from setuptools import setup, find_packages
from pip.req import parse_requirements
import uuid
import sys

AUTHOR = 'Nekmo'
EMAIL = 'contacto@nekmo.com'
PLUGIN_NAME = 'polls'
DESCRIPTION = ''
WEBSITE = 'http://nekmo.com'
DOWNLOAD_URL = ''
STATUS_LEVEL = 1  # 1:Planning 2:Pre-Alpha 3:Alpha 4:Beta 5:Production/Stable 6:Mature 7:Inactive

CLASSIFIERS = [
    'License :: OSI Approved :: MIT License',
    # 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    # 'License :: OSI Approved :: BSD License',
]

ROOT_INCLUDE = ['requirements.txt', 'VERSION', 'LICENSE.txt']
SETUP_REQUIRES = ['pip']

##############################################################################
# find_package_data is an Ian Bicking creation.

# Provided as an attribute, so you can append to these instead
# of replicating them:
standard_exclude = ('*.py', '*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build',
                                './dist', 'EGG-INFO', '*.egg-info')


def find_package_data(where='.', package='',
                      exclude=standard_exclude,
                      exclude_directories=standard_exclude_directories,
                      only_in_packages=True,
                      show_ignored=False):
    """
    Return a dictionary suitable for use in ``package_data``
    in a distutils ``setup.py`` file.

    The dictionary looks like::

        {'package': [files]}

    Where ``files`` is a list of all the files in that package that
    don't match anything in ``exclude``.

    If ``only_in_packages`` is true, then top-level directories that
    are not packages won't be included (but directories under packages
    will).

    Directories matching any pattern in ``exclude_directories`` will
    be ignored; by default directories with leading ``.``, ``CVS``,
    and ``_darcs`` will be ignored.

    If ``show_ignored`` is true, then all the files that aren't
    included in package data are shown on stderr (for debugging
    purposes).

    Note patterns use wildcards, or can be exact paths (including
    leading ``./``), and all searching is case-insensitive.

    This function is by Ian Bicking.
    """

    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "Directory %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append(
                        (fn, prefix + name + '/', package, only_in_packages)
                    )
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "File %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out
##############################################################################

__dir__ = os.path.abspath(os.path.dirname(__file__))


def get_url(dep):
    if hasattr(dep, 'url'):
        return dep.url
    if dep.link is None:
        return
    return dep.link.url


VERSION = open('VERSION').read().replace('\n', '')  # Please, change VERSION file

requirements = parse_requirements('requirements.txt', session=uuid.uuid1())  # Please, change requirements.txt file
INSTALL_REQUIRES = [str(ir.req) for ir in requirements if not get_url(ir)]

try:
    LONG_DESCRIPTION = open('README', 'rt').read()  # Please, change README file
except IOError:
    LONG_DESCRIPTION = ''

if not DESCRIPTION:
    DESCRIPTION = '%s, a plugin for NekBot, a modular and multiprotocol bot written in Python.' % PLUGIN_NAME

STATUS_NAME = ['Planning', 'Pre-Alpha', 'Alpha', 'Beta',
               'Production/Stable', 'Mature', 'Inactive'][STATUS_LEVEL - 1]

packages = find_packages(__dir__)
# Prevent include symbolic links
for package_name in tuple(packages):
    path = os.path.join(__dir__, package_name.replace('.', '/'))
    if not os.path.exists(path):
        continue
    if not os.path.islink(path):
        continue
    packages.remove(package_name)

setup(
    name='nekbot.plugins.%s' % PLUGIN_NAME,
    namespace_packages=['nekbot.plugins'],
    version=VERSION,

    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,

    author=AUTHOR,
    author_email=EMAIL,

    url=WEBSITE,
    
    download_url=DOWNLOAD_URL,

    classifiers=CLASSIFIERS.extend([
        'Development Status :: %i - %s' % (STATUS_LEVEL, STATUS_NAME),
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Communications :: Conferencing',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]),

    platforms=['linux'],

    scripts=[
        # 'scripts/myscript.sh'
    ],
    
    provides=['nekbot.plugins.%s' % PLUGIN_NAME],
    
    install_requires=INSTALL_REQUIRES,

    setup_requires=SETUP_REQUIRES,

    packages=['nekbot', 'nekbot.plugins', 'nekbot.plugins.%s' % PLUGIN_NAME],
    include_package_data=True,

    keywords=['nekbot', 'bot', PLUGIN_NAME, 'plugins', 'chat'],

    entry_points={
    },

    zip_safe=False,
)