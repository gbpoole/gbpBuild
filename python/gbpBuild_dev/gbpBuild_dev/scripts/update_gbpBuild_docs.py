import os
import subprocess
import sys
import git
import click

# Find the project root directory
git_repo = git.Repo(os.path.realpath(__file__), search_parent_directories=True)
dir_root = git_repo.git.rev_parse("--show-toplevel")
dir_python = os.path.abspath(os.path.join(dir_root,"python"))

# Include the path to the local python development packages
sys.path.append(os.path.abspath(os.path.join(dir_python,"gbpBuild_dev")))

# Include the project development module
import gbpBuild_dev.project as prj
import gbpBuild_dev.docs    as docs

@click.command()
def update_gbpBuild_docs():
    # Set/fetch all the project details we need
    project=prj.project()

    # Generate the main project .rst index file
    # and any needed API files as well
    docs.generate_project_rsts(project)

# Permit script execution
if __name__ == '__main__':
    status = update_gbpBuild_docs()
    sys.exit(status)