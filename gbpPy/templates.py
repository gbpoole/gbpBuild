import gbpPy.log as SID
import shutil
import os
import re

# Helper functions
# ----------------

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def check_and_remove_trailing_occurance(txt_in, occurance):
    n_occurance = len(occurance)
    if (txt_in[-n_occurance:] == occurance):
        txt_out = txt_in[0:-n_occurance]
        flag_found = True
    else:
        txt_out = txt_in
        flag_found = False
    return txt_out, flag_found

def parse_template_filename(filename_in):
    # Remove any leading '_dot_'s from the output file name
    filename_out = filename_in.replace("_dot_", ".", 1)

    # Check if the file is a link (and remove any trailing '.link's)
    filename_out, flag_is_link = check_and_remove_trailing_occurance(filename_out, '.link')

    # If not a link, check if it is a template file
    if (not flag_is_link):
        filename_out, flag_is_template = check_and_remove_trailing_occurance(filename_out, '.template')
    else:
        flag_is_template = False

    return filename_out, flag_is_template, flag_is_link

# Get project name from given project directory
def get_base_name(project_dir_abs):
    head, tail = os.path.split(project_dir_abs)
    if (tail == ''):
        head, tail = os.path.split(head)
    return (tail)

# This function locates all annotated parameter references in a line
def find_parameter_references(line):
    regex = re.compile("%\w*%")
    matches = []
    for match in regex.finditer(line):
        param = {}
        param['name']=match.group().strip('%')
        param['span']=match.span()
        matches.append(param)
    return matches

def perform_parameter_substitution(line,parameters):
    regex = re.compile("%\w*%")
    line_new = line
    match = regex.search(line_new)
    while(match):
        line_new = line_new[0:match.start()]+str(parameters[match.group().strip('%')])+line_new[match.end():]
        match = regex.search(line_new)
    return line_new

# Process files
def process_file(file_i,full_path_out,parameters=None):
    if(file_i['is_link']):
        os.symlink(file_i['full_path_in'], full_path_out)
    elif(file_i['is_template']):
        with open(file_i['full_path_in'],"r") as file_in:
            with open(full_path_out,"w") as file_out:
                for line in file_in:
                    file_out.write(perform_parameter_substitution(line,parameters))
    else:
        shutil.copy2(file_i['full_path_in'], full_path_out)

# Define main class
# -----------------

class template:
    def __init__(self,template_name,path=None):

        # If path wasn't given, then check for an environment variable
        if (not path):
            path=os.environ.get('GBPPY_TEMPLATE_PATH')

        # If nothing was found in the environment, check local path
        if (not path):
            path='./'

        # Search the path for the template
        path_list=path.split(':')
        template_dir_abs = None
        for path_i in path_list:
            dir_test  = os.path.join(path_i,template_name)
            if(os.path.isdir(dir_test)):
                template_dir_abs = dir_test
                break

        # Raise an exception if the template was not in the path
        if(not template_dir_abs):
            raise IsADirectoryError("Could not find template '%s' in template path {%s}"%(template_name,path))

        # template_name may have path information. Clean that up.
        template_path_dir,template_name = os.path.split(template_dir_abs)

        # Proceed with template construction
        self.path = template_path_dir
        self.dir = template_dir_abs
        self.name = template_name
        self.directories = []
        self.files = []
        self.n_template_files = 0

        # Parse the template directory
        SID.log.open( "Loading template {'%s' from %s}..." %(self.name,self.path))
        for root, dirs, files in os.walk(self.dir):
            # Parse directories
            dir_dict = {}
            dir_dict['full_path_in' ] = os.path.abspath(root)
            dir_dict['name' ]         = os.path.relpath(os.path.abspath(root),self.dir)

            # Exclude the root directory of the template
            if (os.path.realpath(dir_dict['full_path_in']) != os.path.realpath(self.dir)):
                self.directories.append(dir_dict)

            # Parse files
            for file_i in files:
                name_out, flag_is_template, flag_is_link = parse_template_filename(file_i)
                file_dict = {}
                file_dict['dir_name']= dir_dict['name']
                file_dict['full_path_in']=os.path.join(dir_dict['full_path_in'],file_i )
                file_dict['name_in']= file_i
                file_dict['name_out']= name_out
                file_dict['is_template']= flag_is_template
                file_dict['is_link']= flag_is_link
                if(file_dict['is_template']):
                    self.n_template_files+=1
                self.files.append(file_dict)

        # Search all files to generate a list of needed parameters
        if(self.n_template_files>0):
            SID.log.open("Scanning template files for parameters...")
            self.parameters = set()
            for file_i in [f for f in self.files if(f['is_template'])]:
                with open(file_i['full_path_in'],'r') as file_in:
                    for line in file_in:
                        param_refs = find_parameter_references(line)
                        for param_ref_i in param_refs:
                            self.parameters.add(param_ref_i['name'])
            SID.log.close("Done")

        SID.log.comment("n_directories=%d"%(len( self.directories)))
        SID.log.comment("n_files      =%d"%(len( self.files)))
        SID.log.comment("n_parameters =%d"%(len( self.parameters)))
        for param_ref_i in self.parameters:
            SID.log.comment("   -> %s" % (param_ref_i))

        SID.log.close("Done")

    # Process directories
    def process_directories(self, dir_install, parameters=None, uninstall=False,silent=False):
        if (uninstall):
            SID.log.open("Removing directories...")
            flag_reverse_sort = True
        else:
            SID.log.open("Processing directories...")
            flag_reverse_sort = False
        # Process in sorted order to ensure that the sub-directory structure is respected
        for dir_i in sorted(self.directories, key=lambda k: len(k['name']), reverse=flag_reverse_sort):
            name_out = os.path.normpath(os.path.join(dir_install ,dir_i['name']))
            SID.log.open("Processing directory {%s}..." % (dir_i['name']))
            try:
                if (not os.path.isdir(name_out)):
                    raise IsADirectoryError
                if (uninstall):
                    if(not silent):
                        os.rmdir(name_out)
                        SID.log.close("removed.")
                    else:
                        SID.log.close("removed silently.")
                else:
                    SID.log.close("exists.")
            except:
                if (uninstall):
                    SID.log.close("not found.")
                else:
                    if(not silent):
                        os.mkdir(name_out)
                        SID.log.close("created.")
                    else:
                        SID.log.close("created silently.")
        SID.log.close("Done")

    # Process files
    def process_files(self,dir_install,parameters=None,uninstall=False,silent=False):
        if (uninstall):
            SID.log.open("Removing files...")
        else:
            SID.log.open("Processing files...")
        for file_i in self.files:
            full_path_out = os.path.normpath(os.path.join(dir_install, file_i['dir_name'], file_i['name_out']))
            SID.log.open("Processing file {%s}..." % (os.path.normpath(os.path.join(file_i['dir_name'],file_i['name_out']))))
            try:
                os.stat(full_path_out)
                if (uninstall):
                    if(not silent):
                        os.remove(full_path_out)
                        SID.log.close("removed.")
                    else:
                        SID.log.close("removed silently.")
                else:
                    SID.log.close("exists.")
            except:
                if (uninstall):
                    SID.log.close("not found.")
                else:
                    if(not silent):
                        process_file(file_i,full_path_out,parameters=parameters)
                        SID.log.close("created.")
                    else:
                        SID.log.close("created silently.")
        SID.log.close("Done")

    # Install template
    def install(self,dir_out,parameters=None,silent=False):
        # Check that all the needed template parameters are in the given dictionary
        for param_i in self.parameters:
            if not param_i in parameters:
                SID.log.error("Required parameter {%s} is not present in template installation dictionary."%(param_i))

        # Note that the order needs to be such that directories are created *before* files
        SID.log.open("Installing template {%s}..."%(self.name))
        self.process_directories(dir_out,parameters=parameters,silent=silent)
        self.process_files(dir_out,parameters=parameters,silent=silent)
        SID.log.close("Done")

    # Uninstall template
    def uninstall(self,dir_out,silent=False):
        # Note that the order needs to be such that directories are removed *after* files
        SID.log.open("Removing template {%s}..."%(self.name))
        self.process_files(dir_out,uninstall=True,silent=silent)
        self.process_directories(dir_out, uninstall=True, silent=silent)
        SID.log.close("Done")