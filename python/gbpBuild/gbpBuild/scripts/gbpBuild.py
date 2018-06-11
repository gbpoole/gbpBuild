#! /usr/bin/env python
import os
import sys

import click

import gbpBuild as bld
from .. import templates as tmp
from .. import log as SID

# Main function
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('template_name',default=None,type=str)
@click.argument('output_dir',default=None,type=str)
@click.option('-d','--path','template_path', help='Path to template directory',    type=str,default=None)
@click.option('-r',         'flag_uninstall',help='Remove template',                        default=False,is_flag=True)
@click.option('-s',         'flag_silent',   help='Silent/test run',                        default=False,is_flag=True)
@click.option('-f',         'flag_force',    help='Force write for existing files',         default=False,is_flag=True)
@click.option('-u',         'update_element',help='Update single element only',    type=str,default=None)
def gbpBuild(template_name,output_dir,template_path,flag_uninstall,flag_silent,flag_force,update_element):

    # Validate inputs
    if(not os.path.isdir(output_dir)):
        SID.log.error("Given project directory (%s) is not a valid directory."%(output_dir))

    # Process inputs
    output_dir_abs = os.path.abspath(output_dir)
    project_name    = tmp.get_base_name(output_dir_abs).replace("-", "_")

    # Create list of input templates
    template_list=template_name.split(',')

    ## End parsing of command line
    if(update_element==None):
        SID.log.open("Creating new project (name=%s)..."%(project_name))
    else:
        SID.log.open("Updating element %s in %s..."%(update_element,project_name))

    ## Load the template(s)
    template = tmp.template()
    for template_name in template_list:
        template.add(template_name,path=[template_path,bld.full_path_datafile('templates')])

    ## Process the template
    if(flag_uninstall):
        template.uninstall(output_dir_abs,params_raw=params,silent=flag_silent,update=update_element)
    else:
        ## Generate parameter dictionary
        params = {}
        params['name'] = project_name
        params['author'] = 'Gregory B. Poole'
        params['author_email'] = 'gbpoole@gmail.com'
        params['description'] = 'One line description of project.'

        ## Install template
        template.install(output_dir_abs, params_raw=params, silent=flag_silent,update=update_element,force=flag_force)

    SID.log.close("Done")

# Permit script execution
if __name__ == '__main__':
    status = gbpBuild()
    sys.exit(status)
