#!/usr/bin/env python

from distutils.core import setup

from setuptools import setup, find_packages
from codecs import open
from os import path
import subprocess
import re, os

# Read the version file in the project directory
PROJECT_DIRECTORY = path.abspath(path.dirname(__file__))+'/../../'
VERSIONFILE=os.path.join(PROJECT_DIRECTORY,".version")
version_string = None
with open(VERSIONFILE,'rt') as fp:
    version_string = fp.read().strip()
if version_string==None or version_string=="":
    raise RuntimeError("Unable to load version string from %s." % (VERSIONFILE,))

print('Current `setup.py` version:',version_string)

setup(name='gbpPy_dev',
      version=version_string,
      description="Python code supporting development operations (documenation building, etc.) for the gbpPy project.",
      author='Gregory B. Poole',
      author_email='gbpoole@gmail.com',
      packages=find_packages(),
     )

