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

def perform_parameter_substitution(line,params):
    regex = re.compile("%\w*%")
    line_new = line
    match = regex.search(line_new)
    while(match):
        line_new = line_new[0:match.start()]+str(params[match.group().strip('%')])+line_new[match.end():]
        match = regex.search(line_new)
    return line_new

# Define main classes
# -------------------

class template_directory:
    def __init__(self,dirname_template,dirname):
        # Verify that dirname points to a directory
        if(not os.path.isdir(dirname)):
            raise IsADirectoryError("Directory name {%s} passed to template_directory constructor does not point to a valid directory."%(dirname))

        # Express names relative to the root of the template
        dirname_rel_template = os.path.normpath(os.path.relpath(os.path.abspath(dirname), dirname_template))

        # Set basic properties
        self.parse_name(dirname_rel_template)
        self._template_path    = os.path.normpath(os.path.dirname(dirname_rel_template))
        self._full_path_in_abs = os.path.abspath(dirname)
        self.files             = []
        self.dirname_template  = dirname_template

        # Check if this directory is a symlink
        if(os.path.islink(dirname)):
            self.is_symlink=True
        else:
            self.is_symlink=False

    def parse_name(self,dirname_rel_template):

        self.name_in = os.path.basename(dirname_rel_template)

        # Remove any leading '_dot_'s from the output file name
        self.name_out = self.name_in.replace("_dot_", ".", 1)
    
        # Check if the file is a link (and remove any trailing '.link's)
        self.name_out, self.is_link = check_and_remove_trailing_occurance(self.name_out, '.link')

    def is_root(self):
        return os.path.realpath(self.full_path_in()) == os.path.realpath(self.dirname_template)

    def full_path_in(self):
        return os.path.normpath(self._full_path_in_abs)

    def full_path_out(self,dir_install):
        return os.path.normpath(os.path.normpath(os.path.join(dir_install, self._template_path, self.name_out )))

    def template_path_in(self):
        return os.path.normpath(os.path.join(self._template_path, self.name_in))

    def template_path_out(self):
        return os.path.normpath(os.path.join(self._template_path, self.name_out))

    def install(self,dir_install,silent=False):
        try:
            if( not self.is_root()):
                if(os.path.isdir(self.full_path_out(dir_install))):
                    SID.log.comment("Directory %s exists."%(self.full_path_out(dir_install)))
                else:
                    if(self.is_link):
                        symlink_path=os.path.relpath(self.full_path_in(),os.path.dirname(self.full_path_out(dir_install)))
                    if(not silent):
                        if(self.is_link):
                            if(os.path.lexists(self.full_path_out(dir_install))):
                                os.unlink(self.full_path_out(dir_install))
                                os.symlink(symlink_path,self.full_path_out(dir_install))
                                SID.log.comment("Directory %s link updated." % (self.full_path_out(dir_install)))
                            else:
                                os.symlink(symlink_path,self.full_path_out(dir_install))
                                SID.log.comment("Directory %s linked."%(self.full_path_out(dir_install)))
                        else:
                            os.mkdir(self.full_path_out(dir_install))
                            SID.log.comment("Directory %s created."%(self.full_path_out(dir_install)))
                    else:
                        if(self.is_link):
                            SID.log.comment("Directory %s linked silently."%(self.full_path_out(dir_install)))
                        else:
                            SID.log.comment("Directory %s created silently."%(self.full_path_out(dir_install)))
            else:
                if(os.path.isdir(self.full_path_out(dir_install))):
                    SID.log.comment("Directory %s -- root valid." % (self.full_path_out(dir_install)))
                else:
                    raise NotADirectoryError
        except:
            SID.log.error("Failed to install directory {%s}."%(self.full_path_out()))

    def uninstall(self,dir_install,silent=False):
        try:
            if( not self.is_root()):
                if( not os.path.isdir(self.full_path_out(dir_install))):
                    SID.log.close("Not found.")
                else:
                    if(not silent):
                        if(self.is_link):
                            os.unlink(self.full_path_out(dir_install))
                            SID.log.close("Unlinked.")
                        else:
                            os.rmdir(self.full_path_out(dir_install))
                            SID.log.close("Removed.")
                    else:
                        if(self.is_link):
                            SID.log.close("Unlinked silently.")
                        else:
                            SID.log.close("Removed silently.")
            else:
                SID.log.close("Root ignored.")
        except:
            SID.log.error("Failed to uninstall directory {%s}."%(self.name_out))

    def add_file(self,file_add):
        if(self.is_symlink):
            raise Exception("Can not add file {%s} to symlinked directory {%s}."%(file_add.name_in,self.name_in))
        self.files.append(file_add)

class template_file:
    def __init__(self,filename,dir_host=None):
        # Default to the present directory if one is not passed
        if(not dir_host):
            dir_host=template_directory('.')

        # Set basic properties
        self.parse_name(filename)
        self.dir = dir_host

        # Verify that filename points to a file
        if(not os.path.isfile(self.full_path_in())):
            raise FileNotFoundError("File name {%s} passed to template_file constructor does not point to a valid file."%(self.full_path_in()))

        # Check if this file is a symlink
        if(os.path.islink(filename)):
            self.is_symlink=True
        else:
            self.is_symlink=False

    def parse_name(self,filename):

        self.name_in = filename

        # Remove any leading '_dot_'s from the output file name
        self.name_out = self.name_in.replace("_dot_", ".", 1)
    
        # Check if the file is a link (and remove any trailing '.link's)
        self.name_out, self.is_link = check_and_remove_trailing_occurance(self.name_out, '.link')
    
        # If not a link, check if it is a template file
        if (not self.is_link):
            self.name_out, self.is_template = check_and_remove_trailing_occurance(self.name_out, '.template')
        else:
            self.is_template = False

    def full_path_in(self):
        return os.path.normpath(os.path.join(self.dir.full_path_in(),self.name_in))

    def full_path_out(self,dir_install):
        return os.path.normpath(os.path.join(self.dir.full_path_out(dir_install), self.name_out))

    def template_path_in(self):
        return os.path.normpath(os.path.join(self.dir.template_path_in(), self.name_in))

    def template_path_out(self):
        return os.path.normpath(os.path.join(self.dir.template_path_out(), self.name_out))

    def install(self,dir_install,params=None,silent=False):
        try:
            if(os.path.isfile(self.full_path_out(dir_install))):
                SID.log.comment("   --> %s exists."%(self.full_path_out(dir_install)))
            else:
                if(self.is_link):
                    symlink_path=os.path.relpath(self.full_path_in(),self.dir.full_path_out(dir_install))
                if(not silent):
                    if(self.is_link):
                        if(os.path.lexists(self.full_path_out(dir_install))):
                            os.unlink(self.full_path_out(dir_install))
                            os.symlink(symlink_path,self.full_path_out(dir_install))
                            SID.log.comment("   --> %s link updated." % (self.full_path_out(dir_install)))
                        else:
                            os.symlink(symlink_path,self.full_path_out(dir_install))
                            SID.log.comment("   --> %s linked."%(self.full_path_out(dir_install)))
                    else:
                        self.write_with_substitution(dir_install,params=params)
                        SID.log.comment("   --> %s created."%(self.full_path_out(dir_install)))
                else:
                    if(self.is_link):
                        SID.log.comment("   --> %s linked silently."%(self.full_path_out(dir_install)))
                    else:
                        SID.log.comment("   --> %s created silently."%(self.full_path_out(dir_install)))
        except:
            SID.log.error("Failed to install file {%s}."%(self.full_path_out(dir_install)))

    def uninstall(self,dir_install,silent=False):
        try:
            if( not os.path.isfile(self.full_path_out(dir_install))):
                SID.log.comment("   --> %s not found." % (self.full_path_out(dir_install)))
            else:
                if(not silent):
                    if(self.is_link):
                        os.unlink(self.full_path_out(dir_install))
                        SID.log.comment("   --> %s unlinked."%(self.full_path_out(dir_install)))
                    else:
                        os.remove(self.full_path_out(dir_install))
                        SID.log.comment("   --> %s removed."%(self.full_path_out(dir_install)))
                else:
                    if(self.is_link):
                        SID.log.comment("   --> %s unlinked silently."%(self.full_path_out(dir_install)))
                    else:
                        SID.log.comment("   --> %s removed silently."%(self.full_path_out(dir_install)))
        except:
            SID.log.error("Failed to uninstall file {%s}."%(self.full_path_out(dir_install)))

    def write_with_substitution(self,dir_install,params=None):
        try:
            if(self.is_link):
                os.symlink(os.path.relpath(self.full_path_in(),os.path.dirname(self.full_path_out(dir_install))),self.full_path_out(dir_install))
            elif(self.is_template):
                with open(self.full_path_in(),"r") as fp_in:
                    with open(self.full_path_out(dir_install),"w") as fp_out:
                        for line in fp_in:
                            fp_out.write(perform_parameter_substitution(line,params))
            else:
                shutil.copy2(self.full_path_in(), self.full_path_out(dir_install))
        except:
            SID.log.error("Failed write template file {%s}."%(self.name_in))

class template:
    def __init__(self,template_name,path=None):

        # If path wasn't given, then check for an environment variable
        if (not path):
            path=os.environ.get('GBPPY_TEMPLATE_PATH')

        # If nothing was found in the environment, check local path
        if (not path):
            path='./:./templates/'

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

        # Parse the template directory (n.b.: os.walk() does not follow symlinks by default)
        SID.log.open( "Loading template {'%s' from %s}..." %(self.name,self.path))
        n_template_files = 0
        for root, dirs, files in os.walk(self.dir):

            # Create directory from directory name
            dir_new = template_directory(self.dir,root)

            # Add directory to the list
            self.directories.append(dir_new)

            # Check for symlinks to directories.  This is necessary
            # because os.walk() does not list symlinks to directories
            # and it is less work to look for them manually then to 
            # walk the tree with them and weed-out everything under
            # them which we don't want to consider at all.
            for test_dir_i in os.listdir(root):
                test_dir=os.path.join(dir_new.full_path_in(),test_dir_i)
                if(os.path.islink(test_dir) and os.path.isdir(test_dir)):
                    self.directories.append(template_directory(self.dir,test_dir))

            # Add files
            for file_i in files:
                file_new=template_file(file_i,dir_new)
                if(file_new.is_template):
                    n_template_files+=1
                dir_new.add_file(file_new)

        # Search all files to generate a list of needed parameters
        if(n_template_files>0):
            SID.log.open("Scanning template files for parameters...")
            self.params = set()
            for dir_i in self.directories:
                for file_i in [f for f in dir_i.files if(f.is_template)]:
                    with open(file_i.full_path_in(),'r') as file_in:
                        for line in file_in:
                            param_refs = find_parameter_references(line)
                            for param_ref_i in param_refs:
                                self.params.add(param_ref_i['name'])
            SID.log.close("Done")

        SID.log.comment("n_directories=%d"%(len(self.directories)))
        SID.log.comment("n_files      =%d"%(    self.n_files()))
        SID.log.comment("n_parameters =%d"%(len(self.params)))
        for param_ref_i in self.params:
            SID.log.comment("   --> %s" % (param_ref_i))

        # Print the contents of the template
        self.print()

        SID.log.close("Done")

    # Count the number of files in the template
    def n_files(self):
        n_files =0
        for dir_i in self.directories:
            n_files += len(dir_i.files)
        return n_files

    # Print the template contents
    def print(self):
        SID.log.open("Template contents:")
        for dir_i in self.directories:
            SID.log.comment("Directory {%s}:"%(dir_i.full_path_in()))
            for file_i in dir_i.files:
                SID.log.comment("   --> %s"%(file_i.full_path_in()))
        SID.log.close()

    # Install or uninstall a template
    def _process_template(self, dir_install, params=None, uninstall=False,silent=False):
        if (not uninstall):
            SID.log.open("Installing template {%s} to {%s}..."%(self.name,self.dir))
            flag_reverse_sort = False
        else:
            flag_reverse_sort = True
            SID.log.open("Uninstalling template {%s} from {%s}..."%(self.name,self.dir))

        # Process directories in sorted order to ensure that
        # the sub-directory structure is respected
        for dir_i in sorted(self.directories, key=lambda k: len(k._full_path_in_abs), reverse=flag_reverse_sort):
            # Note the different ordering of directory processing
            # vs. file processing between install/uninstall cases
            if (not uninstall):
                dir_i.install(dir_install,silent=silent)
            else:
                SID.log.open("Uninstalling directory %s..." % (dir_i.full_path_out(dir_install)))

            for file_i in dir_i.files:
                if(uninstall):
                    file_i.uninstall(dir_install,silent=silent)
                else:
                    file_i.install(dir_install,params=params,silent=silent)

            if(uninstall):
                dir_i.uninstall(dir_install,silent=silent)

        SID.log.close("Done.")

    # Install template
    def install(self,dir_out,params=None,silent=False):
        # Check that all the needed template parameters are in the given dictionary
        for param_i in self.params:
            if not param_i in params:
                SID.log.error("Required parameter {%s} is not present in template installation dictionary."%(param_i))
        self._process_template(dir_out,params=params,silent=silent)

    # Uninstall template
    def uninstall(self,dir_out,silent=False):
        self._process_template(dir_out,uninstall=True,silent=silent)

