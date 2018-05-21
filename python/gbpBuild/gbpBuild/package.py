import os
import yaml
import shutil
import git
import filecmp
import gbpBuild as bld
import gbpBuild.log as SID

def find_in_parent_path(path_start,filename_search,check=True):
    # Initialize the start
    path_result = None
    if(os.path.isdir(path_start)):
        cur_dir = path_start
    else:
        cur_dir = os.path.dirname(path_start)

    # Scan upwards until we find the file or run out of path
    while(True):
        filename_test = os.path.join(cur_dir,filename_search)
        if(os.path.isfile(filename_test)):
            path_result = cur_dir
            break
        elif (cur_dir == os.sep):
            break
        else:
            cur_dir = os.path.dirname(cur_dir)

    # Check if the file has been found
    if(check and path_result == None):
        SID.log.error("Could not find {%s} in parent directories of path {%s}."%(filename_search,path_start))

    return path_result

class package:
    """
    This class provides a package object, storing package parameters which describe the package.

    No arguments are needed.  It will scan backwards from the location of this source file
    to the first encountered .git directory.  In that directory, it will look for a .package.yml
    file and make/update a local copy.  If we are not in a git repo, then we are in an installed
    version of the package.  Either way, all parameters are read from this local copy.

    Inputs: path_call; this needs to be the path to a file or directory living somewhere in the package
    """
    def __init__(self,path_call):


        # Scan upwards from the given path until 'setup.py' is found.  That will be the package root.
        self.path_package_root = find_in_parent_path(path_call,"setup.py")

        # Assume that the tail of the root path is the package name
        self.package_name = os.path.dirname(self.path_package_root)

        # Assume that all package modules, etc are in a directory off the root with the package name
        self.path_package = os.path.join(self.path_package_root,self.package_name)

        # Read the package file
        with open_package_file(self.path_package_root) as file_in:
            self.params = file_in.load()
        
        # Assemble a list of data files to bundle with the package
        self.package_files = self.collect_package_files()

    def collect_package_files(self,directory='data'):
        """
        Generate a list of non-code files to be included in the package.
    
        By default, all files in the 'data' directory in the package root will be added.
        :param directory: The path to walk to generate the file list.
        :return: a list of filenames.
        """
        paths = []
        for (path, directories, filenames) in os.walk(os.path.join(self.path_package,directory),followlinks=True):
            for filename in filenames:
                paths.append(os.path.join('..', path, filename))
        return paths

    def __str__(self):
        """
        Convert dictionary of package parameters to a string.
        :return: string
        """
        result ="Package information:\n"
        result+="--------------------\n"
        for k, v in sorted(self.params.items()):
            result+='   ' + k + " = " + str(v) + '\n'

        return result

class package_file():
    def __init__(self,path_package_root):
        # File pointer
        self.fp = None

        # Assume this filename for the package file
        self.filename_package_filename = '.package.yml'

        # Set the filename of the package copy of the package file
        self.filename_package_file = os.path.join(path_package_root,self.filename_package_filename)

    def open(self):
        try:
            SID.log.open("Opening package...")
            self.fp=open(self.filename_package_file)
            SID.log.close("Done.")
        except:
            SID.log.error("Could not open package file {%s}."%(self.filename))
            raise

    def close(self):
        try:
            self.fp.close()
        except:
            SID.log.error("Could not close package file {%s}."%(self.filename))
            raise

    def load(self):
        try:
            params_list = yaml.load(self.fp)
        except:
            SID.log.error("Could not load package file {%s}."%(self.filename))
            raise
        finally:
            return {k: v for d in params_list for k, v in d.items()}

class open_package_file:
    """ Open package file."""

    def __init__(self,path_call):
        self.path_call = path_call

    def __enter__(self):
        # Open the package's copy of the file
        SID.log.open("Opening package file...")
        try:
            self.file_in = package_file(self.path_call)
            self.file_in.open()
        except:
            SID.log.error("Could not open package file.")
            raise
        finally:
            SID.log.close("Done.")
            return self.file_in

    def __exit__(self,*exc):
        self.file_in.close()
        return False
