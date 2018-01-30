#! /usr/bin/env python

import os
import subprocess
import sys
import git
import glob

# Find the project root directory
git_repo = git.Repo(os.path.realpath(__file__), search_parent_directories=True)
dir_root = git_repo.git.rev_parse("--show-toplevel")
dir_python = os.path.abspath(os.path.join(dir_root,"python"))

# Include the path to the local python development packages
sys.path.append(os.path.abspath(os.path.join(dir_python,"gbpPy_dev")))

# Include the project development module
import gbpPy_dev.project as prj
import gbpPy_dev.docs    as docs

def main(argv=None):
    # Set/fetch all the project details we need
    project=prj.project()

    # Generate the main project .rst index file
    docs.generate_project_rsts(project)

# Permit script execution
if __name__ == '__main__':
    status = main()
    sys.exit(status)
