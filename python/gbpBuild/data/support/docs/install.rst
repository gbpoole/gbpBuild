.. _Installation:

Installation
============

This section describes how to download and install this project.

To install the packages associated with this project, they need to be downloaded and installed as follows:

.. code-block:: console

    $ cd /path/to/src/dir
    $ git clone https://github.com/GIT_USER/REPO_NAME
    $ cd REPO_NAME
    $ make init
    $ make install

.. note:: A makefile is provided in the project directory to ease the use of this software project.  Type `make help` for a list of options.
.. warning:: Make sure that the `make init` line is run first-thing before installing.  It will ensure that all needed dependencies are present in your current Python environment.
    Make sure to re-run this line before re-installing, if you change Python environments.

