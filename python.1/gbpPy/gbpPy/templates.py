import filecmp
import os
import re
import shutil

import gbpPy.log as SID

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

def format_template_names(name_list):
    name_txt = ''
    for i_name, name_i in enumerate(name_list):
        if (i_name == 0):
            name_txt += name_i
        else:
            name_txt += ',' + name_i
    return name_txt

_protected_inputs = ['_DIRNAME_LOCAL','_PARAMETERS.key','_PARAMETERS.value']

# Define main classes
# -------------------

class template_directory:
    def __init__(self,dirname_template,full_path_in):
        # Verify that full_path_in points to a directory
        if(not os.path.isdir(full_path_in)):
            raise IsADirectoryError("Directory name {%s} passed to template_directory constructor does not point to a valid directory."%(full_path_in))

        # Express names relative to the root of the template
        #dirname_rel_template = os.path.normpath(os.path.relpath(full_path_in, dirname_template))
        dirname_rel_template = dirname_template

        # Set basic properties
        self.parse_name(dirname_rel_template)
        self._template_path    = os.path.normpath(os.path.dirname(dirname_rel_template))
        self._full_path_in_abs = os.path.abspath(full_path_in)
        self.files             = []
        self.dirname_template  = dirname_template

        # Check if this directory is a symlink
        if(os.path.islink(full_path_in)):
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

    def full_path_out(self,dir_install,template):
        dir_out=template.perform_parameter_substitution_filename(self,dir_install)
        template_path=template.perform_parameter_substitution_filename(self,self._template_path)
        name_out=template.perform_parameter_substitution_filename(self,self.name_out)
        return os.path.normpath(os.path.normpath(os.path.join(dir_out, template_path, name_out )))

    def template_path_in(self):
        return os.path.normpath(os.path.join(self._template_path, self.name_in))

    def template_path_out(self,template):
        template_path=template.perform_parameter_substitution_filename(self,self._template_path)
        name_out=template.perform_parameter_substitution_filename(self,self.name_out)
        return os.path.normpath(os.path.join(template_path, name_out))

class template_file:
    def __init__(self,filename,dir_host):
        # Default to the present directory if one is not passed
        if(not dir_host):
            dir_host=template_directory('.',os.path.abspath('.'))

        # Set basic properties
        self.parse_name(filename)
        self.dir_host = dir_host

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
        return os.path.normpath(os.path.join(self.dir_host.full_path_in(), self.name_in))

    def full_path_out(self,dir_install,template):
        name_out=template.perform_parameter_substitution_filename(self,self.name_out)
        return os.path.normpath(os.path.join(self.dir_host.full_path_out(dir_install, template), name_out))

    def template_path_in(self):
        return os.path.normpath(os.path.join(self.dir_host.template_path_in(), self.name_in))

    def template_path_out(self,template):
        name_out=template.perform_parameter_substitution_filename(self,self.name_out)
        return os.path.normpath(os.path.join(self.dir_host.template_path_out(template), name_out))

    def write_with_substitution(self,dir_install,template):
        try:
            if(self.is_link):
                os.symlink(os.path.relpath(self.full_path_in(),os.path.dirname(self.full_path_out(dir_install,template))),self.full_path_out(dir_install,template))
            elif(self.is_template):
                with open(self.full_path_in(),"r") as fp_in:
                    with open(self.full_path_out(dir_install,template),"w") as fp_out:
                        for line_in in fp_in:
                            for line_out in template.perform_parameter_substitution(self,line_in):
                                fp_out.write(line_out)
            else:
                shutil.copy2(self.full_path_in(), self.full_path_out(dir_install,template))
        except:
            SID.log.error("Failed write template file {%s}."%(self.name_in))

class template:
    def __init__(self,template_name=None,path=None):

        self.path = []
        self.dir = []
        self.name = []
        self.directories = []
        self.params = []
        self.params_list = []
        self.current_element = None

        if(template_name!=None):
            self.add(template_name,path=path)

    # This function locates all annotated parameter references in a line
    def collect_parameter_references(self,line,delimiter="%"):
        if(delimiter==None):
            delimiter="%"
        regex = re.compile("%s[\w:._]*%s"%(delimiter,delimiter))
        for match in regex.finditer(line):
            # Check if there are any directives in the match
            directive = match.group().strip(delimiter)
            if(directive not in _protected_inputs):
                self.params_list.add(directive)

    def init_inputs(self,user_params):

        # Create protected inputs
        self.params = []
        self.params.append({'name': '_PARAMETERS.key',   'input':[key for key in user_params.keys()]})
        self.params.append({'name': '_PARAMETERS.value', 'input':[val for val in user_params.values()]})

        # Add user-defined list
        for param_i_key,param_i_value in user_params.items():
            if(hasattr(param_i_value, '__iter__') and not isinstance(param_i_value, str)):
                self.params.append({'name':param_i_key,'input':param_i_value})
            else:    
                self.params.append({'name':param_i_key,'input':[param_i_value]})

        # Check that all the needed template parameters are in 
        # either the protected or the given dictionary
        for param_i in user_params:
            if not param_i in [d['name'] for d in self.params] and param_i not in _protected_inputs:
                SID.log.error("Required parameter {%s} is not present in template installation dictionary."%(param_i))

    def resolve_directive(self, element, directive):
        if(directive=='_DIRNAME_LOCAL'):
            dir_temp = element.template_path_in()
            if(hasattr(element,'dir')):
            else:
                dir_temp=
            print("ZZZZZ0",element.name_in)
            dir_temp = os.path.dirname(element.full_path_out("",self))
            print("ZZZZZ1")
            input_return = {'name': '_DIRNAME_LOCAL', 'input': [os.path.basename(dir_temp)]}
            print("ZZZZZ2")
        else:
            # Find the entry
            input_return = None
            for input_i in self.params:
                if(input_i['name']==directive):
                    input_return = input_i
                    break
        return input_return

    def _perform_parameter_substitution_ith(self,element,line,idx=None,delimiter="%"):
        if(delimiter==None):
            delimiter="%"
        line_new = line
        n_lines = 1
        print('a:',line,'-',element.name_in,'-')
        if(self.params!=None):
            regex = re.compile("%s[\w:._]*%s"%(delimiter,delimiter))
            match = regex.search(line_new)
            while(match):
                # Strip the delimiters from the match
                #directive = match.group().strip(delimiter)
                directive = match.group()
                directive = directive[len(delimiter):len(directive)-len(delimiter)]
                # First pass: check that input.size() is 1 or current size >1
                param_insert=self.resolve_directive(element, directive)
                if(param_insert!=None):
                    replace_with = param_insert['input']
                else:
                    replace_with = [directive]
                print('b',directive,param_insert,match.group(),match.group().strip(delimiter),replace_with)
                param_insert_size=len(replace_with)
                if(param_insert_size>1):
                    if(n_lines==1):
                        n_lines=param_insert_size
                    elif(param_insert_size!=1 and n_lines!=param_insert_size):
                        SID.log.error("There is an input list size incompatibility (%d!=%d) in {%s}."%(n_lines,param_insert_size,line))
                # Perform substitution
                if(idx==None):
                    line_new = line_new[0:match.start()]+str(replace_with[0])+line_new[match.end():]
                else:
                    line_new = line_new[0:match.start()]+str(replace_with[idx])+line_new[match.end():]
                match = regex.search(line_new)
        if(idx==None):
            return n_lines,line_new
        else:
            return line_new
    
    def perform_parameter_substitution(self,element,line):
        # As a first attempt, assume all subsitutions are of scalars.
        # If in the course of trying to do this, >=1 subsitution(s)
        # is/are a list, then subsequently deal with that.  If the
        # assumption is correct, we will have a string at the end
        # that we can sue.
        n_lines,line_new = self._perform_parameter_substitution_ith(element,line)

        # If one of the parameters is iterable, we generate a set of lines instead.
        lines_new = []
        if(n_lines>1):
            for idx in range(n_lines):
                lines_new.append(self._perform_parameter_substitution_ith(element,line,idx=idx))
        else:
            lines_new.append(line_new)
        return lines_new
    
    def perform_parameter_substitution_filename(self,element,filename_in):
        # Finally, perform substitution
        print('A:',element.name_in)
        n_lines,filename_out = self._perform_parameter_substitution_ith(element,filename_in,delimiter="_var_")
    
        # Check that we haven't used an iterable for the substitution
        if(n_lines!=1):
            SID.log.error("An invalid filename parameter substitution has occured for {%s} (n_lines=%d)."%(filename_in,n_lines))
    
        return filename_out

    def _process_directory_recursive(self,full_path_start,template_start,n_template_files):
        # Parse the given template directory
        for root, dirs, files in os.walk(full_path_start):
            # Create directory from directory name
            template_path=os.path.normpath(os.path.join(template_start,os.path.relpath(root,full_path_start)))
            dir_new = template_directory(template_path,root)

            # Add directory to the list
            self.add_directory(dir_new)

            # Check for symlinks to directories.  This is necessary
            # because os.walk() does not list symlinks to directories
            # and it is less work to look for them manually then to 
            # walk the tree with them and weed-out everything under
            # them which we don't want to consider at all.
            for test_dir_i in os.listdir(root):
                test_dir=os.path.join(dir_new.full_path_in(),test_dir_i)
                if(os.path.islink(test_dir) and os.path.isdir(test_dir)):
                    # Resolve the link
                    test_dir=os.path.abspath(os.path.join(root,os.readlink(test_dir)))
                    # Process paths underneith symlinked template directories
                    # if they are not marked as being links
                    template_path=os.path.normpath(os.path.join(template_start,os.path.relpath(os.path.join(root,test_dir_i),full_path_start)))
                    dir_link = template_directory(template_path,test_dir)
                    if(not dir_link.is_link):
                        n_template_files=self._process_directory_recursive(test_dir,template_path,n_template_files)
                    # ...else, just add the path
                    else:
                        self.add_directory(dir_link)

            # Add files
            for file_i in files:
                file_new=template_file(file_i,dir_new)
                if(file_new.is_template):
                    n_template_files+=1
                self.add_file(file_new)

        return(n_template_files)

    def add(self,template_name,path=None):
        # If path wasn't given, then check for an environment variable
        if (not path):
            path=os.environ.get('GBPPY_TEMPLATE_PATH')

        # If nothing was found in the environment, check local path
        if (not path):
            path='./templates/'

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
        self.path.append(template_path_dir)
        self.dir.append(template_dir_abs)
        self.name.append(template_name)

        # Walk the template directory structure, recursively processing symlinked directories
        SID.log.open( "Loading template {'%s' from %s}..." %(self.name[-1],self.path[-1]))
        n_template_files = self._process_directory_recursive(self.dir[-1],'',0)

        # Search all files to generate a list of needed parameters
        self.params_list = set()
        if(n_template_files>0):
            SID.log.open("Scanning template files for parameters...")
            for dir_i in self.directories:
                self.collect_parameter_references(dir_i.full_path_in(),delimiter="_var_")
                for file_i in [f for f in dir_i.files if(f.is_template)]:
                    self.collect_parameter_references(file_i.full_path_in(),delimiter="_var_")
                    with open(file_i.full_path_in(),'r') as file_in:
                        for line in file_in:
                            self.collect_parameter_references(line,delimiter="%")
            SID.log.close("Done")

        # Print the contents of the template
        self.print()

        SID.log.close("Done")

    def update_element(self,element,update):
        # If no update element is given, then we're updating everythong
        if(update==None):
            return True

        # Check if this is the update element
        if(element.template_path_out(self)==update):
            return True

        # Compute the element's full output path and use that to make comparisons.
        # Also get the name of the directory it's sitting in 
        element_path_out = element.template_path_out(self)
        element_dir = os.path.dirname(element_path_out)

        # ... else, check if this element sits within the directory structure of the update element
        parent_path_out=os.path.dirname(element_path_out)
        is_in_update_path=(parent_path_out==update)
        while parent_path_out!='' and not is_in_update_path:
            parent_path_out=os.path.dirname(parent_path_out)
            is_in_update_path=(parent_path_out==update)
        return (is_in_update_path)

    def get_directory(self,template_path_out):
        for dir_i in self.directories:
            if(dir_i.template_path_out(self)==template_path_out):
                return dir_i
        return None

    def get_file(self,template_path_out):
        for dir_i in self.directories:
            for file_i in dir_i.files:
                if(file_i.template_path_out(self)==template_path_out):
                    return file_i
        return None

    def add_directory(self,dir_add):
        dir_check = self.get_directory(dir_add.template_path_out(self))
        if(dir_check==None):
            self.directories.append(dir_add)

    def add_file(self, file_add):
        # Prevent the addition of files to symlinked directories
        if (file_add.dir_in.is_symlink):
            raise Exception("Can not add file {%s} to symlinked directory {%s}." % (file_add.name_in, file_add.dir_in.name_in))

        # Check if we should be adding this file to an existing directory
        dir_check = self.get_directory(file_add.dir_in.template_path_out(self))
        if(dir_check==None):
            dir_out = file_add.dir_in
        else:
            dir_out = dir_check
        # Check if this file already exists
        file_check = self.get_file(file_add.template_path_out(self))

        # ... if it does, check for conflicts
        if(file_check != None):
            if(not filecmp.cmp(file_add.full_path_in(),file_check.full_path_in())):
                SID.log.error("There is a file incompatability between template files '%s' and '%s'."%(file_add.full_path_in(),file_check.full_path_in()))

        # Append file to list if it's new
        if(file_check == None):
            dir_out.files.append(file_add)

    # Count the number of files in the template
    def n_files(self):
        n_files =0
        for dir_i in self.directories:
            n_files += len(dir_i.files)
        return n_files

    # Print the template contents
    def print(self):
        SID.log.open("Template contents:")
        SID.log.comment("n_directories=%d"%(len(self.directories)))
        SID.log.comment("n_files      =%d"%(    self.n_files()))
        SID.log.comment("n_parameters =%d"%(len(self.params_list)))
        for param_ref_i in self.params_list:
            SID.log.comment("   --> %s" % (param_ref_i))

        for dir_i in sorted(self.directories, key=lambda dir_j: len(dir_j.template_path_out(self))):
            SID.log.open("Directory {%s}:"%(dir_i.template_path_out(self)))
            for file_i in sorted(dir_i.files, key=lambda file_j: file_j.template_path_out(self)):
                SID.log.comment("--> %s"%(file_i.template_path_out(self)))
            SID.log.close()
        SID.log.close()

    # Install or uninstall a template
    def _process_template(self, dir_install, params=None, uninstall=False,silent=False,update=None,force=False):
        name_txt = format_template_names(self.name)
        if (not uninstall):
            if(len(self.name)>1):
                SID.log.open("Installing templates {%s} to {%s}..."%(name_txt,dir_install))
            else:
                SID.log.open("Installing template {%s} to {%s}..."%(name_txt,dir_install))
            flag_reverse_sort = False
        else:
            flag_reverse_sort = True
            if(len(self.name)>1):
                SID.log.open("Uninstalling templates {%s} from {%s}..."%(name_txt,dir_install))
            else:
                SID.log.open("Uninstalling template {%s} from {%s}..."%(name_txt,dir_install))

        # Process directories in sorted order to ensure that
        # the sub-directory structure is respected
        for dir_i in sorted(self.directories, key=lambda k: len(k.full_path_out(dir_install,self)), reverse=flag_reverse_sort):
            # Note the different ordering of directory processing
            # vs. file processing between install/uninstall cases
            self.current_element = dir_i
            if (not uninstall and self.update_element(dir_i,update)):
                self.install_directory(dir_i,dir_install,silent=silent,force=force)
            elif(self.update_element(dir_i,update)):
                SID.log.open("Uninstalling directory %s..." % (dir_i.full_path_out(dir_install,params)))

            for file_i in dir_i.files:
                self.current_element = file_i
                if(uninstall and self.update_element(file_i,update)):
                    self.uninstall_file(file_i,dir_install,silent=silent)
                elif(self.update_element(file_i,update)):
                    self.install_file(file_i,dir_install,silent=silent,force=force)

            self.current_element = dir_i
            if(uninstall and self.update_element(dir_i,update)):
                self.uninstall_directory(dir_i,dir_install,silent=silent)
            elif(self.update_element(dir_i,update)):
                SID.log.close()

        SID.log.close("Done.")

    def install_directory(self,directory,dir_install,silent=False,force=None):
        full_path_out = directory.full_path_out(dir_install,self)
        try:
            if( not directory.is_root()):
                if(os.path.isdir(full_path_out)):
                    SID.log.open("Directory %s exists."%(full_path_out))
                else:
                    # Figure-out the relative path directly to the linked file
                    if(directory.is_link):
                        symlink_path=os.path.relpath(directory.full_path_in(),os.path.dirname(full_path_out))
                    if(not silent):
                        if(directory.is_link):
                            if(os.path.lexists(full_path_out)):
                                os.unlink(full_path_out)
                                os.symlink(symlink_path,full_path_out)
                                SID.log.open("Directory %s link updated." % (full_path_out))
                            else:
                                os.symlink(symlink_path,full_path_out)
                                SID.log.open("Directory %s linked."%(full_path_out))
                        else:
                            os.mkdir(full_path_out)
                            SID.log.open("Directory %s created."%(full_path_out))
                    else:
                        if(directory.is_link):
                            if(os.path.lexists(full_path_out)):
                                SID.log.open("Directory %s link updated silently."%(full_path_out))
                            else:
                                SID.log.open("Directory %s linked silently."%(full_path_out))
                        else:
                            SID.log.open("Directory %s created silently."%(full_path_out))
            else:
                if(os.path.isdir(full_path_out)):
                    SID.log.open("Directory %s -- root valid." % (full_path_out))
                else:
                    raise NotADirectoryError
        except:
            SID.log.error("Failed to install directory {%s}."%(full_path_out))

    def uninstall_directory(self,directory,dir_install,silent=False):
        full_path_out = directory.full_path_out(dir_install,self)
        try:
            if( not directory.is_root()):
                if( not os.path.isdir(full_path_out)):
                    SID.log.close("Not found.")
                else:
                    if(not silent):
                        if(directory.is_link):
                            os.unlink(full_path_out)
                            SID.log.close("Unlinked.")
                        else:
                            os.rmdir(full_path_out)
                            SID.log.close("Removed.")
                    else:
                        if(directory.is_link):
                            SID.log.close("Unlinked silently.")
                        else:
                            SID.log.close("Removed silently.")
            else:
                SID.log.close("Root ignored.")
        except:
            SID.log.error("Failed to uninstall directory {%s}."%(directory.name_out))

    def install_file(self,file_install,dir_install,silent=False,force=False):
        full_path_in  = file_install.full_path_in()
        full_path_out = file_install.full_path_out(dir_install,self)
        try:
            flag_file_exists=os.path.isfile(file_install.full_path_out(dir_install,self))
            if(flag_file_exists and not force):
                SID.log.comment("--> %s exists."%(full_path_out))
            else:
                if(file_install.is_link):
                    symlink_path=os.path.relpath(full_path_in,file_install.dir_in.full_path_out(dir_install,self))
                if(not silent):
                    if(file_install.is_link):
                        if(os.path.lexists(full_path_out)):
                            os.unlink(full_path_out)
                            os.symlink(symlink_path,full_path_out)
                            SID.log.comment("--> %s link updated." % (full_path_out))
                        else:
                            os.symlink(symlink_path,full_path_out)
                            SID.log.comment("--> %s linked."%(full_path_out))
                    else:
                        if(flag_file_exists):
                            os.remove(full_path_out) 
                            SID.log.comment("--> %s removed."%(full_path_out))
                        file_install.write_with_substitution(dir_install,self)
                        if(flag_file_exists):
                            SID.log.comment("--> %s updated."%(full_path_out))
                        else:
                            SID.log.comment("--> %s created."%(full_path_out))
                else:
                    if(file_install.is_link):
                        if(os.path.lexists(full_path_out)):
                            SID.log.comment("--> %s link updated silently."%(full_path_out))
                        else:
                            SID.log.comment("--> %s linked silently."%(full_path_out))
                    else:
                        if(flag_file_exists):
                            SID.log.comment("--> %s updated silently."%(full_path_out))
                        else:
                            SID.log.comment("--> %s created silently."%(full_path_out))
        except:
            SID.log.error("Failed to install file {%s}."%(full_path_out))

    def uninstall_file(self,file_install,dir_install,silent=False):
        full_path_out = file_install.full_path_out(dir_install,self)
        try:
            if( not os.path.isfile(full_path_out)):
                SID.log.comment("--> %s not found." % (full_path_out))
            else:
                if(not silent):
                    if(file_install.is_link):
                        os.unlink(full_path_out)
                        SID.log.comment("--> %s unlinked."%(full_path_out))
                    else:
                        os.remove(full_path_out)
                        SID.log.comment("--> %s removed."%(full_path_out))
                else:
                    if(file_install.is_link):
                        SID.log.comment("--> %s unlinked silently."%(full_path_out))
                    else:
                        SID.log.comment("--> %s removed silently."%(full_path_out))
        except:
            SID.log.error("Failed to uninstall file {%s}."%(full_path_out))


    # Install template
    def install(self,dir_out,params_raw=None,silent=False,update=None,force=False):
        # Create a list of project parameters, which includes the user parameters
        # we've been passed as well as the protected variables
        self.init_inputs(params_raw)

        # Perform install
        self._process_template(dir_out,silent=silent,update=update,force=force)

    # Uninstall template
    def uninstall(self,dir_out,params_raw=None,silent=False,update=None):
        # Create a list of project parameters, which includes the user parameters
        # we've been passed as well as the protected variables
        self.init_inputs(params_raw)

        # Perform uninstall
        self._process_template(dir_out,uninstall=True,silent=silent,update=update)
