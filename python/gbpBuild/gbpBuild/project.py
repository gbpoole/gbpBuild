import yaml
import shutil
import git
import filecmp

import os
import sys

# Make sure that what's in this path takes precidence
# over an installed version of the project
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

import gbpBuild as bld
import gbpBuild.log as SID

class project:
    """
    This class provides a project object, storing project parameters which describe the project.

    No arguments are needed.  It will scan backwards from the location of this source file
    to the first encountered .git directory.  In that directory, it will look for a .project.yml
    file and make/update a local copy.  If we are not in a git repo, then we are in an installed
    version of the project.  Either way, all parameters are read from this local copy.

    Inputs: path_call; this needs to be the path to a file or directory living somewhere in the project
    """
    def __init__(self,path_call):
        # Store the path_call
        self.path_call = path_call

        # Assume this filename for the project file
        self.filename_project_filename = '.project.yml'
        self.filename_auxiliary_filename = '.project_aux.yml'

        # Set the filename of the package copy of the project file
        self.filename_project_file = os.path.join(bld._PACKAGE_ROOT,self.filename_project_filename)
        self.filename_auxiliary_file = os.path.join(bld._PACKAGE_ROOT,self.filename_auxiliary_filename)

        # Determine if we are in a project repository.  Set to None if not.
        self.path_project_root = None
        self.filename_project_file_source = None
        with git.Repo(os.path.realpath(self.path_call), search_parent_directories=True) as git_repo:
            self.path_project_root = git_repo.git.rev_parse("--show-toplevel")
            self.filename_project_file_source = os.path.normpath(os.path.join(self.path_project_root,self.filename_project_filename))

        # Read the project file
        with open_project_file(self) as file_in:
            self.params = file_in.load()

    def add_packages_to_path(self):
        """
        Import all the python packages belonging to this project.
        """
        dir_file = os.path.abspath(self.path_project_root)
        count = 0
        for (directory, directories, filenames) in os.walk(dir_file):
            for filename in filenames:
                # Exclude gbpBuild (load it independently) for the case
                # that we're running this within that package.
                if(filename=="setup.py" and directory!="gbpBuild"):
                    path_package = os.path.abspath(directory)
                    sys.path.insert(0,path_package)
                    count+=1
                    break
        return count

    def __str__(self):
        """
        Convert dictionary of project parameters to a string.
        :return: string
        """
        result ="Project information:\n"
        result+="--------------------\n"
        for k, v in sorted(self.params.items()):
            result+='   ' + k + " = " + str(v) + '\n'

        return result

class project_file():
    def __init__(self,project):
        self.project=project

        # File pointer
        self.fp_prj = None
        self.fp_aux = None

        # Update the project file
        self.update()

    def update(self):

        # Check if we are inside a project repository...
        if(self.project.path_project_root):
            # ... if so, update the package's copy of the project file.  This is needed because if
            #    this is being run from an installed package, then there is no access to files outside
            #    of the package, and we need to work with an up-to-date copy instead.
            SID.log.open("Validating package's project file...")
            try:
                flag_update=False
                if(not os.path.isfile(self.project.filename_project_file)):
                    flag_update=True
                elif(not filecmp.cmp(self.project.filename_project_file_source,self.project.filename_project_file)):
                    flag_update=True
                if(flag_update):
                    # Make a copy of the project file
                    shutil.copy2(self.project.filename_project_file_source,self.project.filename_project_file)
                    SID.log.close("Updated.")
                else:
                    SID.log.close("Up-to-date.")
            except:
                SID.log.error("Could not update package's project file.")
                raise

            # Create a dictionary of a bunch of auxiliary project information

            # Set some project directories
            aux_params = []
            aux_params.append({'dir_docs': os.path.abspath(os.path.join(self.project.path_project_root, "docs"))})
            aux_params.append({'dir_docs_api_src': os.path.abspath(os.path.join(self.project.path_project_root, "docs/src"))})
            aux_params.append({'dir_docs_build': os.path.abspath(os.path.join(self.project.path_project_root, "docs/_build"))})
            aux_params.append({'dir_python': os.path.abspath(os.path.join(self.project.path_project_root, "python"))})
            aux_params.append({'dir_python_pkg': os.path.abspath(os.path.join(self.project.path_project_root, 'python/gbpBuild/'))})

            # Check if this is a C-project (the appropriate makefile will be present if so)
            if(os.path.isfile(os.path.join(self.project.path_project_root, ".Makefile-c"))):
                aux_params.append({'is_C_project': True})
            else:
                aux_params.append({'is_C_project': False})

            # Check if this is a Python-project (the appropriate makefile will be present if so)
            if(os.path.isfile(os.path.join(self.project.path_project_root, ".Makefile-py"))):
                aux_params.append({'is_Python_project': True})
            else:
                aux_params.append({'is_Python_project': False})

            # Extract version & release from .version file.
            try:
                with open("%s/.version" % (self.project.path_project_root), "r") as fp_in:
                    version_string_source = str(fp_in.readline()).strip('\n')
                    aux_params.append({'version': version_string_source}) 
            except BaseException:
                SID.log.comment("Project '.version' file not found.  Setting version='unset'")
                aux_params.append({'version': 'unset'})

            ## TODO: Need to split version from release.
            aux_params.append({'release': version_string_source})

            # Write auxiliary parameters file
            with open(self.project.filename_auxiliary_file, 'w') as outfile:
                yaml.dump(aux_params, outfile, default_flow_style=False)


    def open(self):
        try:
            SID.log.open("Opening project...")
            self.fp_prj=open(self.project.filename_project_file)
            self.fp_aux=open(self.project.filename_auxiliary_file)
            SID.log.close("Done.")
        except:
            SID.log.error("Could not open project file {%s}."%(self.project.filename))
            raise

    def close(self):
        try:
            self.fp_prj.close()
            self.fp_aux.close()
        except:
            SID.log.error("Could not close project file {%s}."%(self.project.filename))
            raise

    def load(self):
        try:
            params_list = []
            params_list.append(yaml.safe_load(self.fp_prj))
            params_list.append(yaml.safe_load(self.fp_aux))
            # Add a few extra things
            params_list.append([{'path_project_root':self.project.path_project_root}])
        except:
            SID.log.error("Could not load project file {%s}."%(self.project.filename))
            raise
        finally:
            result = dict()
            for params in params_list:
                result.update({k: v for d in params for k, v in d.items()})
            return result

class open_project_file:
    """ Open project file."""

    def __init__(self,project):
        self.project = project

    def __enter__(self):
        # Open the package's copy of the file
        SID.log.open("Opening project file...")
        try:
            self.file_in = project_file(self.project)
            self.file_in.open()
        except:
            SID.log.error("Could not open project file.")
            raise
        finally:
            SID.log.close("Done.")
            return self.file_in

    def __exit__(self,*exc):
        self.file_in.close()
        return False
