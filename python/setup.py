#!/usr/bin/env python

import os
import re
import subprocess
from codecs import open
from distutils.core import setup
from os import path

from setuptools import find_packages, setup

# The following code which handles versioning was patterned after 
# a solution posted by 'Sven' here:
#
# https://stackoverflow.com/questions/6786555/automatic-version-number-both-in-setup-py-setuptools-and-source-code

# Read the version file in the project directory
PROJECT_DIRECTORY = path.abspath(path.dirname(__file__))+'/../'
VERSIONFILE=os.path.join(PROJECT_DIRECTORY,".version")
version_string = None
with open(VERSIONFILE,'rt') as fp:
    version_string = fp.read().strip()
if version_string==None or version_string=="":
    raise RuntimeError("Unable to load version string from %s." % (VERSIONFILE,))

# Check that there's a git repository in the project directory
if os.path.exists(os.path.join(PROJECT_DIRECTORY, '.git')):
    # Get the hash of the HEAD commit
    cmd = 'git rev-parse --verify --short HEAD'
    git_hash = subprocess.check_output(cmd, shell=True, universal_newlines=True).strip()
    # Get the list of project tags
    tags =  [tag.strip() for tag in subprocess.check_output('git tag', shell=True, universal_newlines=True).strip().split('\n')]
    # If the tag in the version file is not in the list of project tags ...
    git_version_string = 'v'+version_string
    if not git_version_string in tags:
        # ... then add that tag to the HEAD commit
        cmd = 'git tag -a %s %s -m "tagged by setup.py"' % (git_version_string, git_hash)        
        print('Quitting before I run cmd:',cmd)
        exit(1)
        subprocess.check_output(cmd, shell=True, universal_newlines=True)
    # Add the git hash to the version we will use in setup.py
    version_string += ', git hash: %s' % git_hash
else:
    raise RuntimeError("Unable to find the project's git repository at %s." % (PROJECT_DIRECTORY,))

print('Current `setup.py` version:',version_string)

setup(name='gbpBuild',
      version=version_string,
      description="The gbpBuild library's Python package",
      author='Gregory B. Poole',
      author_email='gbpoole@gmail.com',
      packages=find_packages(),
     )
