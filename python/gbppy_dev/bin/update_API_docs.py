#! /usr/bin/env python

import os
import subprocess
import sys

# Include the project development module
sys.path.append(os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__),'../../gbppy_dev/'))))
import gbppy_dev.project as prj
import gbppy_dev.docs    as docs

def main(argv=None):
    # Set/fetch all the project details we need
    project=prj.project()

    # Generate the main project .rst index file
    docs.generate_project_rsts(project)

# Permit script execution
if __name__ == '__main__':
    status = main()
    sys.exit(status)
