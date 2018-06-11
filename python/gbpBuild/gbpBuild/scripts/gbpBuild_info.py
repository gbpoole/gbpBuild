import sys
import os
import click

# Make sure that what's in this path takes precidence
# over an installed version of the project
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.join(os.path.abspath(__file__),'..'))))

import gbpBuild.project as prj
import gbpBuild.package as pkg
import gbpBuild.docs as docs
import gbpBuild.log as SID

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
def gbpBuild_info():
    """
    Print the dictionary of project parameters stored in the project (.project.yml) and package (.package.yml) files.
    :return: None
    """
    # Set/fetch all the project details we need
    project = prj.project(os.path.abspath(__file__))
    package = pkg.package(os.path.abspath(__file__))

    # Print project & package information
    SID.log.comment('')
    SID.log.comment(project)
    SID.log.comment(package)

# Permit script execution
if __name__ == '__main__':
    status = gbpBuild_info()
    sys.exit(status)
