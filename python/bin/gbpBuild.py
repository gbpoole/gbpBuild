#! /usr/bin/env python
import gbpPy.log       as SID
import gbpPy.cmdl      as cmdl
import gbpPy.templates as tmp
import sys
import os

# Main function
def main(argv=None):

    ## Start parsing of command line

    # Define cmd line positional arguments
    positional_arguments = []
    positional_arguments.append(['template_name',None])
    positional_arguments.append(['project_dir',None])

    # Define cmd line optional arguments.
    optional_arguments = []
    optional_arguments.append([['-d','--path'],'Path to template directory','string',None,'template_path'])
    optional_arguments.append([['-r'],'Uninstall template','bool',False,'flag_uninstall'])
    optional_arguments.append([['-s'],'Silent/test run','bool',False,'flag_silent'])

    # Create argument parser and check syntax
    cmdl_parser = cmdl.parser(argv,positional_arguments,optional_arguments)

    # For readability, create variables to express content of cmd-line
    project_dir_in = cmdl_parser.extract('project_dir')
    template_name  = cmdl_parser.extract('template_name')
    template_path  = cmdl_parser.extract('template_path')
    flag_uninstall = cmdl_parser.extract('flag_uninstall')
    flag_silent    = cmdl_parser.extract('flag_silent')

    # Validate inputs
    if(not os.path.isdir(project_dir_in)):
        SID.log.error("Given project directory (%s) is not a valid directory."%(project_dir_in))

    # Process inputs
    project_dir_abs = os.path.abspath(project_dir_in)
    project_name    = tmp.get_base_name(project_dir_abs)

    ## End parsing of command line

    SID.log.open("Creating new project (name=%s)..."%(project_name))

    ## Load the template
    template = tmp.template(template_name,path=template_path)

    ## Process the template
    if(flag_uninstall):
        template.uninstall(project_dir_abs,silent=flag_silent)
    else:
        ## Generate parameter dictionary
        params = {}
        params['project_name'] = project_name
        params['project_author'] = 'Gregory B. Poole'
        params['kcov_token'] = 'unset'
        params['gbpbuild_rel_path'] = os.path.relpath(os.getcwd(),project_dir_abs)

        ## Install template
        template.install(project_dir_abs, params=params, silent=flag_silent)

    SID.log.close("Done")

# Permit script execution
if __name__ == '__main__':
    status = main()
    sys.exit(status)
