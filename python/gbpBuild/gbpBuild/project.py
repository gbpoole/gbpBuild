import os
import yaml
import shutil
import git
import filecmp
import gbpBuild.log as SID

class project_file():
    def __init__(self):
        self.filename_project_file = '.project.yml'

        self.update()

        return self

    def update(self):

        # Check if we are inside a project repository...
        with git.Repo(os.path.realpath(__file__), search_parent_directories=True) as git_repo:
            path_project_root = git_repo.git.rev_parse("--show-toplevel")

            # ... if so, update the package's copy of the project file.  This is needed because if
            #    this is being run from an installed package, then there is no access to files outside
            #    of the package, and we need to work with an up-to-date copy instead.
            SID.log.open("Validating package's project file...")
            self.filename_project_file_source = os.path.normpath(os.path.join(path_package_root,self.filename_project_file))
            try:
                if(not filecmp.cmp(self.filename_project_file_source)):
                    shutil.copy2(self.filename_project_file_source,self.filename_project_file)

                    # Set some project directories
                    aux_params['dir_docs'] = os.path.abspath(os.path.join(self.dir_root, "docs"))
                    aux_params['dir_docs_api_src'] = os.path.abspath(os.path.join(self.dir_root, "docs/src"))
                    aux_params['dir_docs_build'] = os.path.abspath(os.path.join(self.dir_root, "docs/build"))
                    aux_params['dir_python'] = os.path.abspath(os.path.join(self.dir_root, "python"))
                    aux_params['dir_python_pkg'] = os.path.abspath(os.path.join(self.dir_root, 'python/gbpBuild/'))

                    # Check if this is a C-project (the appropriate makefile will be present if so)
                    if(os.path.isfile(os.path.join(self.dir_root, ".Makefile-c"))):
                        aux_params['is_C_project'] = True
                    else:
                        aux_params['is_C_project'] = False

                    # Check if this is a Python-project (the appropriate makefile will be present if so)
                    if(os.path.isfile(os.path.join(self.dir_root, ".Makefile-py"))):
                        aux_params['is_Python_project'] = True
                    else:
                        aux_params['is_Python_project'] = False

                    # Extract version & release from .version file.
                    try:
                        with open("%s/.version" % (self.dir_root), "r") as fp_in:
                            aux_params['version'] = str(fp_in.readline()).strip('\n')
                    except BaseException:
                        SID.log.comment("Project '.version' file not found.  Setting version='unset'")
                        aux_params['version'] = 'unset'

                    # TODO: Need to split version from release.
                    aux_params['release'] = aux_params['version']

                    SID.log.close("Updated.")
                else:
                    SID.log.close("Up-to-date.")
            except:
                SID.log.error("Could not update package's project file.")
                raise

    def open(self):
        try:
            self.fp=open(self.filename_project_file)
        except:
            SID.log.error("Could not open project file {%s}."%(self.filename))
            raise

    def close(self):
        try:
            close(self.fp)
        except:
            SID.log.error("Could not close project file {%s}."%(self.filename))
            raise

    def load(self):
        try:
            params_list = yaml.load(file_in.fp)
        except:
            SID.log.error("Could not load project file {%s}."%(self.filename))
            raise
        finally:
            return {k: v for d in params_list for k, v in d.items()}

class open_project_file():
    """ Open project file."""

    def __enter__(self):
        # Open the package's copy of the file
        SID.log.open("Opening project file...")
        try:
            self.file_in = project_file()
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

class project:
    """
    This class provides a project object, storing project parameters which describe the project.

    No arguments are needed.  It will scan backwards from the location of this source file
    to the first encountered .git directory.  In that directory, it will look for a .project.yml
    file and make/update a local copy.  If we are not in a git repo, then we are in an installed
    version of the project.  Either way, all parameters are read from this local copy.
    """
    def __init__(self):

        # Read the project file
        with open_project_file() as file_in:
            self.params = file_in.load()

        return self

    def __str__(self):
        """
        Convert dictionary of project parameters to a string.
        :return: string
        """
        result ="Project information:\n"
        result+="--------------------"
        for k, v in sorted(self.params.items()):
            result+='   ' + k + " = " + str(v) + '\n'

        return result
