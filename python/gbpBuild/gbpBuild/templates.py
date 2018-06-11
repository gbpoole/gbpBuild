import filecmp
import os
import sys
import re
import shutil
import fnmatch

# Make sure that what's in this path takes precidence
# over an installed version of the project
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

from . import log as SID

_regex_parameter_selector = "[^%/]*"

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

# Define main classes
# -------------------

class template_element(object):
    def __init__(self, full_path_in_template_root, full_path_in, template_path, dir_host,is_directory=False,is_file=False):

        # Set basic properties
        self.dirname_template = full_path_in_template_root
        self._full_path_in = full_path_in
        self._template_path_in = template_path
        self.parse_name(self._template_path_in)

        # Set the host directory
        self.dir_host = dir_host

        # Check if this directory is a symlink
        self.is_symlink = os.path.islink(full_path_in)

        # Set some flags determining what type of element this is
        self.is_directory=is_directory
        self.is_file=is_file

        # Make sure full_path_in points to actual file
        # if element is a symlink and not marked as a template link
        if(self.is_symlink and not self.is_link):
            self._full_path_in = os.path.realpath(self._full_path_in)

    def parse_name(self, template_path_in):

        self.name_in = os.path.basename(template_path_in)

        # Remove any leading '_dot_'s from the output file name
        self.name_out = self.name_in.replace("_dot_", ".", 1)

        # Check if the file is a link (and remove any trailing '.link's)
        self.name_out, self.is_link = check_and_remove_trailing_occurance(self.name_out, '.link')

    def full_path_in(self):
        return os.path.normpath(os.path.abspath(self._full_path_in))

    def template_path_in(self):
        return self._template_path_in


class template_directory(template_element):
    def __init__(self, full_path_in_template_root, full_path_dir, template_path, dir_host):
        # Verify that full_path_in points to a directory
        if (not os.path.isdir(full_path_dir)):
            raise IsADirectoryError(
                "Directory name {%s} passed to template_directory constructor does not point to a valid directory." % (
                full_path_dir))

        # Call the base-class _init_
        template_element.__init__(self, full_path_in_template_root, full_path_dir, template_path, dir_host, is_directory=True)

        # This will host a list of all files in this directory
        self.files = []

    def is_root(self):
        return os.path.realpath(self.full_path_in()) == os.path.realpath(self.dirname_template)


class template_file(template_element):
    def __init__(self, full_path_in_template_root, full_path_file, template_path, dir_host):
        # Verify that full_path_in points to a file
        if (not os.path.isfile(full_path_file)):
            raise FileNotFoundError(
                "File name {%s} passed to template_file constructor does not point to a valid file." % (full_path_file))

        # Call the base-class _init_
        template_element.__init__(self, full_path_in_template_root, full_path_file, template_path, dir_host, is_file=True)

        # Check if the file is a template (and remove any trailing '.template's)
        self.name_out, self.is_template = check_and_remove_trailing_occurance(self.name_out, '.template')

class template:
    def __init__(self,template_name=None,path=None):

        self.path = []
        self.dir = []
        self.name = []
        self.directories = []
        self.params = []
        self.params_list = []
        self.current_element = None
        self.dir_install = "."

        if(template_name!=None):
            self.add(template_name,path=path)

    # This function locates all annotated parameter references in a string
    def collect_parameter_references(self,string,delimiter="%%%"):
        if(delimiter==None):
            delimiter="%%%"
        regex = re.compile("%s%s%s" % (delimiter,_regex_parameter_selector, delimiter))
        for match in regex.finditer(string):
            # Check if there are any directives in the match
            directive = match.group()
            directive = directive[len(delimiter):len(directive) - len(delimiter)]
            if(not self.resolve_directive(None,directive,check=True)):
                self.params_list.add(directive)

    def init_inputs(self,user_params):

        self.params = user_params

        # Check that all the needed template parameters can be resolved
        for param_i in user_params:
            if not self.resolve_directive(None,param_i,check=True):
                SID.log.error("Required parameter {%s} is not present in template installation dictionary."%(param_i))

    def resolve_directive(self, element, directive, check=False):
        input_return = None
        # Directives starting with '_' are protected commands.
        # Check to see if the directive is defined ...
        if(directive[0:1]=='_'):
            directive_words=directive[1:].split()
            command=directive_words[0]
            directive_args=directive_words[1:]
            n_args=len(directive_args)
            if(command=='DIRNAME_LOCAL'):
                if(n_args!=0):
                    SID.log.error("Syntax error in directive {%s}; no arguments allowed."%(directive))
                if(check):
                    input_return = True
                else:
                    if(element==None):
                        SID.log.error("No element passed to 'resolve_directive()'.")
                    if(element.dir_host!=None):
                        dir_path_out = self.template_path_out(element.dir_host)
                    else:
                        dir_path_out = self.dir_install
                    dirname = os.path.basename(dir_path_out)
                    input_return = {'name': '_DIRNAME_LOCAL', 'input': [dirname]}
            elif(command=="PARAMETERS.key"):
                if(n_args!=0):
                    SID.log.error("Syntax error in directive {%s}; no arguments allowed."%(directive))
                if(check):
                    input_return = True
                else:
                    input_return = {'name': '_PARAMETERS.key',   'input':[key for key in self.params.keys()]} 
            elif(command=="PARAMETERS.value"):
                if(n_args!=0):
                    SID.log.error("Syntax error in directive {%s}; no arguments allowed."%(directive))
                if(check):
                    input_return = True
                else:
                    input_return = {'name': '_PARAMETERS.key',   'input':[key for key in self.params.values()]}
            elif(command.startswith('DIRLIST')):
                # The command can contain subdirectives, separated by underscores
                # Parse this information to determine what sort of list we're making
                command_words=command.split("_")
                n_command_words=len(command_words)
                if(n_command_words==1):
                    list_mode='all'
                elif(n_command_words==2):
                    if(command_words[1]=='DIRS'):
                        list_mode='dirs'
                    elif(command_words[1]=='FILES'):
                        list_mode='files'
                    else:
                        SID.log_error("Invalid directive syntax {%s}; word {%s} invalid."%(line,command_words[1]))
                else:
                    SID.log_error("Invalid directive syntax {%s}; too many command words." % (line))
                if(check):
                    input_return = True
                else:
                    # Because we can't be sure that all the files are present
                    # either in the full input or output path, we need to
                    # generate the list from the elements in the template.  We
                    # may also have some files/directories preexisiting this
                    # template run, and we want to add those as well, so we have
                    # listings which actually represent the current state
                    template_element_list = []
                    dir_host = self.full_path_out(element.dir_host)
                    listing_host = os.listdir(dir_host)
                    if(list_mode=='all' or list_mode=='files'):
                        for file_i in element.dir_host.files:
                            template_element_list.append(os.path.basename(self.full_path_out(file_i)))
                        for element_i in listing_host:
                            if(os.path.isfile(element_i)):
                                if(element_i not in template_element_list):
                                    template_element_list.append(element_i)
                    if(list_mode=='all' or list_mode=='dirs'):
                        for dir_i in self.directories:
                            dir_host_i=os.path.dirname(self.full_path_out(dir_i))
                            if(dir_host==dir_host_i):
                                template_element_list.append(os.path.basename(self.full_path_out(dir_i)))
                            for element_i in listing_host:
                                if (os.path.isdir(element_i)):
                                    if (element_i not in template_element_list):
                                        template_element_list.append(element_i)

                    # Sort the element list
                    template_element_list=sorted(template_element_list)

                    if(n_args==0):
                        listing=template_element_list
                    elif(n_args==1):
                        flag_keep_list = [False] * len(template_element_list)
                        for wildcard in directive_args[0].split(','):
                            # If wildcard is prepended with '!', treat it as a negation search
                            if(wildcard[0:1]=='!'):
                                wildcard=wildcard[1:]
                                flag_wildcard = False
                            else:
                                flag_wildcard = True
                            for i_file,file_i in enumerate(template_element_list):
                                if(fnmatch.fnmatch(file_i,wildcard)):
                                    flag_keep_list[i_file]=flag_wildcard
                        listing = [file_i for (file_i,flag) in zip(template_element_list,flag_keep_list) if flag]
                    else:
                        SID.log.error("Syntax error in directive {%s}; too many arguments."%(directive))
                    input_return = {'name':command,'input':listing}

        # ... else, look to see if it has been listed in the user parameters
        else:
            if(self.params):
                for param_i_key,param_i_value in self.params.items():
                    if(directive==param_i_key):
                        if(check):
                            input_return = True
                        else:
                            if(hasattr(param_i_value, '__iter__') and not isinstance(param_i_value, str)):
                                input_return = {'name':param_i_key,'input':param_i_value}
                            else:
                                input_return = {'name':param_i_key,'input':[param_i_value]}
                        break
        return input_return

    def _perform_parameter_substitution_ith(self,element,line,idx=None,delimiter="%%%"):
        if(delimiter==None):
            delimiter="%%%"
        line_new = line
        n_lines = -1
        if(self.params!=None):
            regex = re.compile("%s%s%s" % (delimiter, _regex_parameter_selector, delimiter))
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
                param_insert_size=len(replace_with)
                # This is just to prevent an infinite loop.  Since
                # param_insert_size==0, this line should be thrown
                # away anyways ... but we want to make sure there
                # are no errors, so we'll substitute this for just
                # to keep things going.
                if(param_insert_size==0):
                    replace_with=["---"]
                # Record n_lines this way to make sure that
                # all parameter substitutions result in the
                # same number of lines
                if(n_lines<0):
                    n_lines=param_insert_size
                elif(n_lines!=param_insert_size):
                    SID.log.error("There is an input list size incompatibility (%d!=%d) in {%s}."%(n_lines,param_insert_size,line))
                # Perform substitution
                if(idx==None):
                    line_new = line_new[0:match.start()]+str(replace_with[0])+line_new[match.end():]
                else:
                    if(idx>len(replace_with)):
                        SID.log_error("Indexing error (%d>%d)for input line {%s}."%(idx,len(replace_with),line))
                    line_new = line_new[0:match.start()]+str(replace_with[idx])+line_new[match.end():]
                match = regex.search(line_new)
        # If n_lines<0, then no parameter substitution has occurred
        # and we will just be returning the input line
        if(n_lines<0):
            n_lines=1
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
        elif(n_lines==1):
            lines_new.append(line_new)
        return lines_new
    
    def perform_parameter_substitution_filename(self,element,name_out=False):
        # Finally, perform substitution
        if(name_out):
            n_lines,filename_out = self._perform_parameter_substitution_ith(element,element.name_out,delimiter="_var_")
        else:
            n_lines,filename_out = self._perform_parameter_substitution_ith(element,element.name_in,delimiter="_var_")

        # Check that we haven't used an iterable for the substitution
        if(n_lines!=1):
            SID.log.error("An invalid filename parameter substitution has occured for {%s} (n_lines=%d)."%(element.full_path_in(),n_lines))
    
        return filename_out

    def _process_directory_recursive(self, full_path_template, full_path_recurse_start, template_path_start, n_template_files):
        # Parse the given template directory
        for root, dirs, files in os.walk(full_path_recurse_start):
            # Create directory from directory name
            full_path_element = os.path.abspath(root)
            template_path_dir=os.path.normpath(os.path.join(template_path_start,os.path.relpath(root,full_path_recurse_start)))
            template_path_parent=os.path.dirname(template_path_dir)
            if(template_path_parent==''):
                template_path_parent='.'
            dir_new = template_directory(full_path_template,full_path_element,template_path_dir,self.get_directory(template_path_parent))

            # Ignore '__pycache__' direcories that can get annoyingly created automatically when templates are installed by setuptools.
            if(os.path.basename(full_path_element)!="__pycache__"):
                # Add directory to the list
                self.add_directory(dir_new)

                # Check for symlinks to directories.  This is necessary
                # because os.walk() does not list symlinks to directories (by default)
                # and it is less work (I think) to look for them manually then to
                # walk the tree with them and weed-out everything under
                # them which we may not (often don't) want to consider at all.
                for test_dir_i in os.listdir(root):
                    # Ignore '__pycache__' direcories that can get annoyingly created automatically when templatess are installed by setuptools.
                    if(os.path.basename(test_dir_i)!="__pycache__"):
                        full_path_element=os.path.join(dir_new.full_path_in(),test_dir_i)
                        if(os.path.islink(full_path_element) and os.path.isdir(full_path_element)):
                            # Sort-out some paths for the link
                            full_path_element=os.path.abspath(os.path.join(root,os.readlink(full_path_element)))
                            template_path_element = os.path.join(template_path_dir,test_dir_i)
                            template_path_parent = os.path.dirname(template_path_element)
                            # Process paths underneath sym-linked template directories
                            # if they are not marked as being links
                            dir_link = template_directory(full_path_template, full_path_element, template_path_element, self.get_directory(template_path_parent))
                            if(not dir_link.is_link):
                                n_template_files=self._process_directory_recursive(full_path_template,full_path_element,template_path_element,n_template_files)
                            # ...else, just add the path
                            else:
                                self.add_directory(dir_link)

                # Add files
                for file_i in files:
                    template_path = os.path.normpath(os.path.join(template_path_start,os.path.relpath(root,full_path_recurse_start),file_i))
                    full_path_element = os.path.join(root,file_i)
                    file_new=template_file(full_path_template, full_path_element, template_path, dir_new)
                    if(file_new.is_template):
                        n_template_files+=1
                    self.add_file(file_new)

        return(n_template_files)

    def _build_path_list(self,path=None):

        # Priority goes to the list of paths passed by the call
        path_list = []
        for path_i in [p for p in path if p!=None]:
            path_list.append(path_i)

        # Then prioritize anyhting in the environment path 
        path_env=os.environ.get('GBPPY_TEMPLATE_PATH')
        if(path_env!=None):
            for path_i in [p for p in path_env.split(':') if p!=None]:
                path_list.append(path_i)

        return(path_list) 

    def add(self,template_name,path=None):

        # Build a list of priority-ordered paths to search
        path_list = self._build_path_list(path)

        # Search the path
        template_dir_abs=None
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

        # Walk the template directory structure, recursively processing sym-linked directories
        SID.log.open( "Loading template {'%s' from %s}..." %(self.name[-1],self.path[-1]))
        n_template_files = self._process_directory_recursive(self.dir[-1],self.dir[-1],'.',0)

        # Search all files to generate a list of needed parameters
        self.params_list = set()
        if(n_template_files>0):
            SID.log.open("Scanning template files for parameters...")
            for dir_i in self.directories:
                self.collect_parameter_references(dir_i.full_path_in(),delimiter="_var_")
                for file_i in [f for f in dir_i.files if(f.is_template)]:
                    self.collect_parameter_references(file_i.full_path_in(),delimiter="_var_")
                    if(file_i.is_template):
                        with open(file_i.full_path_in(),'r') as file_in:
                            for line in file_in:
                                self.collect_parameter_references(line,delimiter="%%%")
            SID.log.close("Done")

        # Print the contents of the template
        SID.log.comment(self)

        SID.log.close("Done")

    def update_element(self,element,update):
        # If no update element is given, then we're updating everything
        if(update==None):
            return True

        # Check if this is the update element
        if(self.template_path_out(element)==update):
            return True

        # Compute the element's full output path and use that to make comparisons.
        # Also get the name of the directory it's sitting in 
        element_path_out = self.template_path_out(element)

        # ... else, check if this element sits within the directory structure of the update element
        parent_path_out=os.path.dirname(element_path_out)
        is_in_update_path=(parent_path_out==update)
        while parent_path_out not in ['','/'] and not is_in_update_path:
            parent_path_out=os.path.dirname(parent_path_out)
            is_in_update_path=(parent_path_out==update)
        return (is_in_update_path)

    def get_directory(self,template_path_in):
        for dir_i in self.directories:
            if(dir_i.template_path_in()==template_path_in):
                return dir_i
        return None

    def get_file(self,template_path_in):
        for dir_i in self.directories:
            for file_i in dir_i.files:
                if(file_i.template_path_in()==template_path_in):
                    return file_i
        return None

    def add_directory(self,dir_add):
        dir_check = self.get_directory(dir_add.template_path_in())
        if(dir_check==None):
            self.directories.append(dir_add)

    def add_file(self, file_add):
        # Prevent the addition of files to sym-linked directories
        if (file_add.dir_host.is_symlink):
            raise Exception("Can not add file {%s} to sym-linked directory {%s}." % (file_add.name_in, file_add.dir_host.name_in))

        # Check if we should be adding this file to an existing directory
        if(file_add.dir_host!=None):
            dir_check = self.get_directory(file_add.dir_host.template_path_in())
        else:
            dir_check = None
        if(dir_check==None):
            dir_out = file_add.dir_host
        else:
            dir_out = dir_check

        # Check if this file already exists
        file_check = self.get_file(file_add.template_path_in())

        # If not, append it to its directory's list
        if(file_check == None):
            dir_out.files.append(file_add)

        # ... else, check for conflicts
        else:
            if(not filecmp.cmp(file_add.full_path_in(),file_check.full_path_in())):
                SID.log.error("There is a file incompatibility between template files '%s' and '%s'."%(file_add.template_path_in(),file_check.template_path_in()))

    # Count the number of files in the template
    def n_files(self):
        n_files =0
        for dir_i in self.directories:
            n_files += len(dir_i.files)
        return n_files

    def full_path_out(self, element):
        if (element.dir_host == None):
            dir_host = self.dir_install
        else:
            dir_host = self.full_path_out(element.dir_host)
        name_out = self.perform_parameter_substitution_filename(element,name_out=True)
        return os.path.normpath(os.path.abspath(os.path.join(dir_host, name_out)))

    def template_path_out(self, element):
        if (element.dir_host == None):
            dir_host = "."
        else:
            dir_host = self.template_path_out(element.dir_host)
        name_out = self.perform_parameter_substitution_filename(element,name_out=True)
        return os.path.normpath(os.path.join(dir_host, name_out))

    def write_with_substitution(self, file_in):
        if(not file_in.is_file):
            SID.log.error("Something other than a file {%s} has been passed to the 'write_with_substitution' template method." % (self.name_in))
        try:
            if(file_in.is_link):
                os.symlink(os.path.relpath(self.full_path_in(file_in), os.path.dirname(self.full_path_out(file_in))),
                           self.full_path_out(file_in))
            elif(file_in.is_template):
                with open(file_in.full_path_in(),"r") as fp_in:
                    with open(self.full_path_out(file_in), "w") as fp_out:
                        for line_in in fp_in:
                            for line_out in self.perform_parameter_substitution(file_in,line_in):
                                fp_out.write(line_out)
            else:
                shutil.copy2(file_in.full_path_in(), self.full_path_out(file_in))
        except:
            SID.log.error("Failed write template file {%s}."%(element.template_path_in()))

    # Print the template contents
    def __str__(self):
        result="Template contents:"
        result+="n_directories=%d"%(len(self.directories))
        result+="n_files      =%d"%(    self.n_files())
        result+="n_parameters =%d"%(len(self.params_list))
        for param_ref_i in self.params_list:
            result+="   --> %s"%(param_ref_i)

        for dir_i in sorted(self.directories, key=lambda dir_j: len(self.template_path_out(dir_j))):
            result+="Directory {%s}:"%(dir_i.template_path_in())
            for file_i in sorted(dir_i.files, key=lambda file_j: self.template_path_out(file_j)):
                result+="   --> %s"%(file_i.template_path_in())

    # Install or uninstall a template
    def _process_template(self, params=None, uninstall=False, silent=False, update=None, force=False):
        name_txt = format_template_names(self.name)
        if (not uninstall):
            if(len(self.name)>1):
                SID.log.open("Installing templates {%s} to {%s}..."%(name_txt,self.dir_install))
            else:
                SID.log.open("Installing template {%s} to {%s}..."%(name_txt,self.dir_install))
            flag_reverse_sort = False
        else:
            flag_reverse_sort = True
            if(len(self.name)>1):
                SID.log.open("Uninstalling templates {%s} from {%s}..."%(name_txt,self.dir_install))
            else:
                SID.log.open("Uninstalling template {%s} from {%s}..."%(name_txt,self.dir_install))

        # Process directories in sorted order to ensure that
        # the sub-directory structure is respected
        for dir_i in sorted(self.directories, key=lambda k: len(self.full_path_out(k)), reverse=flag_reverse_sort):
            # Note the different ordering of directory processing
            # vs. file processing between install/uninstall cases
            self.current_element = dir_i
            if (not uninstall and self.update_element(dir_i,update)):
                self.install_directory(dir_i, silent=silent, force=force)
            elif(self.update_element(dir_i,update)):
                SID.log.open("Uninstalling directory %s..." % (self.full_path_out(dir_i)))

            for file_i in dir_i.files:
                self.current_element = file_i
                if(uninstall and self.update_element(file_i,update)):
                    self.uninstall_file(file_i, silent=silent)
                elif(self.update_element(file_i,update)):
                    self.install_file(file_i, silent=silent, force=force)

            self.current_element = dir_i
            if(uninstall and self.update_element(dir_i,update)):
                self.uninstall_directory(dir_i, silent=silent)
            elif(self.update_element(dir_i,update)):
                SID.log.close()

        SID.log.close("Done.")

    def install_directory(self, directory, silent=False, force=None):
        full_path_out = self.full_path_out(directory)
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

    def uninstall_directory(self, directory, silent=False):
        full_path_out = self.full_path_out(directory)
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

    def install_file(self, file_install, silent=False, force=False):
        full_path_in  = file_install.full_path_in()
        full_path_out = self.full_path_out(file_install)
        try:
            flag_file_exists=os.path.isfile(self.full_path_out(file_install))
            if(flag_file_exists and not force):
                SID.log.comment("--> %s exists."%(full_path_out))
            else:
                if(file_install.is_link):
                    symlink_path=os.path.relpath(full_path_in, self.full_path_out(file_install.dir_in))
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
                        self.write_with_substitution(file_install)
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

    def uninstall_file(self, file_install, silent=False):
        full_path_out = self.full_path_out(file_install)
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
        # Set the current install directory
        self.dir_install=dir_out

        # Create a list of project parameters
        self.init_inputs(params_raw)

        # Perform install
        self._process_template(silent=silent, update=update, force=force)

        # Unset the current install directory
        self.dir_install = "."


    # Uninstall template
    def uninstall(self,dir_out,params_raw=None,silent=False,update=None):
        # Set the current install directory
        self.dir_install=dir_out

        # Create a list of project parameters
        self.init_inputs(params_raw)

        # Perform uninstall
        self._process_template(uninstall=True, silent=silent, update=update)

        # Unset the current install directory
        self.dir_install="."
