#! /usr/bin/env python
import os
import importlib
import sys

import click

# Make sure that what's in this path takes precedence
# over an installed version of the project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.join(os.path.abspath(__file__), '..', '..'))))

import gbpBuild as bld
import gbpBuild.templates as tmp

# Main function
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('template_name', default=None, type=str)
@click.argument('output_dir', default=None, type=str)
@click.option('-d', '--path', 'template_path', help='Path to template directory', type=str, default=None)
@click.option('-r', 'flag_uninstall', help='Remove template', default=False, is_flag=True)
@click.option('-s', 'flag_silent', help='Silent/test run', default=False, is_flag=True)
@click.option('-f', 'flag_force', help='Force write for existing files', default=False, is_flag=True)
@click.option('-u', 'update_element', help='Update single element only', type=str, default=None)
def gbpTemplate(template_name, output_dir, template_path, flag_uninstall, flag_silent, flag_force, update_element):

    # Initialize a dictionary to hold all template paramters
    params = {}

    # ======== Start processing of CMDL ========

    # Validate output directory
    if(not os.path.isdir(output_dir)):
        bld.log.error("Given project directory (%s) is not a valid directory." % (output_dir))
    output_dir_abs = os.path.abspath(output_dir)

    # Try to infer a project name from the output directory
    # and add it to the parameter dictionary if sucessful
    project_name = tmp.get_base_name(output_dir_abs).replace("-", "_")
    params['name'] = project_name

    # Create list of input templates
    template_list = template_name.split(',')

    # End parsing of command line
    if(update_element is None):
        bld.log.open("Creating new project (name=%s)..." % (project_name))
    else:
        bld.log.open("Updating element %s in %s..." % (update_element, project_name))

    # ========= End processing of CMDL =========

    # Load the template(s)
    template = tmp.template()
    for template_name in template_list:
        template.add(template_name, path=[template_path, bld.full_path_datafile('templates')])

    # Process the template
    if(flag_uninstall):
        template.uninstall(output_dir_abs, params_raw=params, silent=flag_silent, update=update_element)
    else:

        # Validate parameters; interactively ask for any missing ones
        template.validate_parameters(interactive=True)

        # Install template
        template.install(output_dir_abs, params_raw=params, silent=flag_silent, update=update_element, force=flag_force)

    bld.log.close("Done")


# Permit script execution
if __name__ == '__main__':
    status = gbpTemplate()
    sys.exit(status)
