#! /usr/bin/env python
import gbpPy.log  as SID
import gbpPy.cmdl as cmdl
import shutil
import sys
import os

SID.log.set_fp(sys.stderr) # Not really needed, since this is the default

# Get project name from given project directory
def get_base_name(project_dir_abs):
    head,tail= os.path.split(project_dir_abs)
    if(tail==''):
        head,tail= os.path.split(head)
    return(tail)

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def check_and_remove_trailing_occurance(txt_in,occurance):
    n_occurance=len(occurance)
    if(txt_in[-n_occurance:]==occurance):
        txt_out=txt_in[0:-n_occurance]
        flag_found=True
    else:
        txt_out=txt_in
        flag_found=False
    return txt_out,flag_found

def parse_template_filename(filename_in):

    # Remove any leading '_dot_'s from the output file name
    filename_out=filename_in.replace("_dot_",".",1)

    # Check if the file is a link (and remove any trailing '.link's)
    filename_out,flag_is_link=check_and_remove_trailing_occurance(filename_out,'.link')

    # If not a link, check if it is a template file
    if(not flag_is_link):
        filename_out,flag_is_template=check_and_remove_trailing_occurance(filename_out,'.template')
    else:
        flag_is_template=False

    return filename_out,flag_is_template,flag_is_link

# Process directories
def process_template_directories(template_directories,uninstall=False):
    if(uninstall):
        SID.log.open("Removing directories...")
    else:
        SID.log.open("Processing directories...")
    for dir_i in template_directories:
        SID.log.open("Processing directory {%s}..."%(dir_i['name_out']))
        try:
            os.stat(dir_i['name_out'])
            if(uninstall):
                os.rmdir(dir_i['full_path_out'])
                SID.log.close("removed.")
            else:
                SID.log.close("exists.")
        except:
            if(uninstall):
                SID.log.close("not found.")
            else:
                os.mkdir(dir_i['name_out'])
                SID.log.close("created.")
    SID.log.close("Done")
    
# Process files
def process_template_files(template_files,uninstall=False):
    if(uninstall):
        SID.log.open("Removing files...")
    else:
        SID.log.open("Processing files...")
    for file_i in template_files:
        SID.log.open("Processing file {%s}->{%s}..."%(file_i['name_out'],file_i['full_path_out']))
        try:
            os.stat(file_i['full_path_out'])
            if(uninstall):
                os.remove(file_i['full_path_out'])
                SID.log.close("removed.")
            else:
                SID.log.close("exists.")
        except:
            if(uninstall):
                SID.log.close("not found.")
            else:
                shutil.copy2(file_i['full_path_in'],file_i['full_path_out'])
                SID.log.close("created.")
    SID.log.close("Done")

# Main function
def main(argv=None):

    # --- Parse command line ---

    ## Define cmd line positional arguments
    ## - Each entry should be a 2-element list; 
    ##      element[0]: is the argument name 
    ##      element[1]: is the default value
    ## - Aguments with default=None are required
    ## - Optional arguments will be assigned values
    ##   in the order they are listed here
    positional_arguments = []
    positional_arguments.append(['project_dir',None])
    positional_arguments.append(['template_dir',None])

    ## Define cmd line optional arguments.  
    ## - These are passed to the standard python
    ##   OptionParser.add_option() method ... see
    ##   documentation on that for more details
    ## - Each element should be a 5-element list:
    ##      element[0]: list of opt_strs (len() must be >0)
    ##      element[1]: help text
    ##      element[2]: storage type
    ##      element[3]: default value
    ##      element[4]: storage key
    ## - Set storage type to 'bool' if you just want a switch.
    ##   The default value will be used to decide its sense.
    optional_arguments = []
    optional_arguments.append([['-r'],'Uninstall template','bool',False,'flag_uninstall'])

    ## Create argument parser and check syntax
    cmdl_parser = cmdl.parser(argv,positional_arguments,optional_arguments)

    ## For readability, create variables to express content of cmd-line
    project_dir_in  = cmdl_parser.extract('project_dir')
    template_dir_in = cmdl_parser.extract('template_dir')
    flag_uninstall  = cmdl_parser.extract('flag_uninstall')

    ## Validate inputs
    if(not os.path.isdir(project_dir_in)):
        SID.log.error("Given project directory (%s) is not a vailid directory."%(project_dir_in))
    if(not os.path.isdir(template_dir_in)):
        SID.log.error("Given template directory (%s) is not a vailid directory."%(template_dir_in))

    # --------------------------

    # Break-down the project directory a bit
    project_dir_rel  = os.path.relpath(project_dir_in)
    project_dir_abs  = os.path.abspath(project_dir_in)
    project_name     = get_base_name(project_dir_abs)
    template_dir_abs = os.path.abspath(template_dir_in)
    template_name    = get_base_name(template_dir_abs)

    SID.log.open("Creating new project (name=%s)..."%(project_name))

    # Parse the template directory
    SID.log.open("Parsing the template directory {%s}..."%(template_name))
    template_directories = []
    template_files = []
    for root, dirs, files in os.walk(template_dir_in):
        # Parse directories
        root_rel_in = os.path.relpath(root,template_dir_in)
        dir_dict = {}
        dir_dict['name_in']=root_rel_in
        dir_dict['name_out']=os.path.normpath(os.path.join(project_dir_in,root_rel_in))
        if(os.path.realpath(dir_dict['name_out'])!=os.path.realpath(project_dir_rel)):
            template_directories.append(dir_dict)

        # Parse files
        for file_i in files:
            full_path_in = os.path.join(root,file_i)
            name_out,flag_is_template,flag_is_link = parse_template_filename(file_i)
            file_dict = {}
            file_dict['name_in']=file_i
            file_dict['full_path_in']=os.path.join(root,file_i)
            file_dict['name_out']=name_out
            file_dict['full_path_out']=os.path.normpath(os.path.join(project_dir_in,root_rel_in,name_out))
            file_dict['is_template_file']=flag_is_template
            file_dict['is_link']=flag_is_link
            template_files.append(file_dict)
    SID.log.comment("n_directories=%d"%(len(template_directories)))
    SID.log.comment("n_files      =%d"%(len(template_files)))
    SID.log.close("Done")

    if(not flag_uninstall):
        SID.log.open("Installing template {%s}..."%(template_name))
        process_template_directories(template_directories)
        process_template_files(template_files)
        SID.log.close("Done")
    else:
        SID.log.open("Removing template {%s}..."%(template_name))
        process_template_files(template_files,uninstall=True)
        process_template_directories(template_directories,uninstall=True)
        SID.log.close("Done")

# Allow script execution
if __name__ == '__main__':
    status = main()
    sys.exit(status)
