#! /usr/bin/env python
import os
import sys

import click

import gbpBuild as bld
import gbpBuild.log as SID
import gbpBuild.templates as tmp

# Main function
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('template_name',default=None,type=str)
@click.argument('project_dir',default=None,type=str)
@click.option('-d','--path','template_path', help='Path to template directory',    type=str,default=None)
@click.option('-r',         'flag_uninstall',help='Remove template',                        default=False,is_flag=True)
@click.option('-s',         'flag_silent',   help='Silent/test run',                        default=False,is_flag=True)
@click.option('-f',         'flag_force',    help='Force write for existing files',         default=False,is_flag=True)
@click.option('-u',         'update_element',help='Update single element only',    type=str,default=None)
def gbpBuild(template_name,project_dir,template_path,flag_uninstall,flag_silent,flag_force,update_element):

    # Validate inputs
    if(not os.path.isdir(project_dir)):
        SID.log.error("Given project directory (%s) is not a valid directory."%(project_dir))

    # Process inputs
    project_dir_abs = os.path.abspath(project_dir)
    project_name    = tmp.get_base_name(project_dir_abs).replace("-", "_")

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
        template.uninstall(project_dir_abs,params_raw=params,silent=flag_silent,update=update_element)
    else:
        ## Generate parameter dictionary
        params = {}
        params['project_name'] = project_name
        params['project_author'] = 'Gregory B. Poole'
        params['project_email'] = 'gbpoole@gmail.com'
        params['project_description'] = 'One line description of project.'
        params['kcov_token'] = 'unset'
        params['gbpbuild_rel_path'] = os.path.relpath(os.getcwd(),project_dir_abs)

        ## Install template
        template.install(project_dir_abs, params_raw=params, silent=flag_silent,update=update_element,force=flag_force)

    SID.log.close("Done")

# Permit script execution
if __name__ == '__main__':
    status = gbpBuild()
    sys.exit(status)
