import os
import sys
import git
import glob
import click

# Import the project development module
import gbpBuild.project as prj
import gbpBuild.docs as docs

# Include the paths to local python projects (including the _dev package)
# Make sure we prepend to the list to make sure that we don't use an
# installed version.  We need access to the information in the
# project directory here.
# for setup_py_i in glob.glob(dir_python + "/**/setup.py", recursive=True):
#    sys.path.insert(0,os.path.abspath(os.path.dirname(setup_py_i)))

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('path_in_project', default=None, type=str)
def update_gbpBuild_docs(path_in_project):
    """Auto-generate the .rst files which describe all the project APIs (both
    C/C++ and Python, if present).

    This function is meant to be called automatically by the "docs-update" target of the project makefile.
    :return: None
    """
    # Set/fetch all the project details we need
    project = prj.project(path_in_project)

    # Generate the main project .rst index file
    # and any needed API files as well
    docs.generate_project_rsts(project)


# Permit script execution
if __name__ == '__main__':
    status = update_gbpBuild_docs()
    sys.exit(status)
