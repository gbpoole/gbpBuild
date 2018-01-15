import os

class project:
    def __init__(self,project_name,dir_root,dir_docs_build):
        self.name = project_name

        self.author = "author"
        self.description = "One line description of project here."

        # Set some project direcories
        self.dir_root    = dir_root
        self.dir_docs    = os.path.join(self.dir_root,"docs")
        self.dir_python  = os.path.join(self.dir_root,"python")

        # Infer the name of the project from the root 

        # Check if this is a C-project (CMakeList.txt will exist if so)
        if(os.path.isfile(os.path.join(self.dir_root,"CMakeLists.txt"))):
            self.is_C_project = True
        else:
            self.is_C_project = True

        # Check if this is a Python-project (the python directory will exist if so)
        if(os.path.isdir(self.dir_python)):
            self.is_Python_project = True
        else:
            self.is_Python_project = True

        # If dir_docs_build is of the format "@...@" then it is *not*
        # being called from cmake ... so assume we are doing a python
        # build.  Otherwise, cmake has performed a variable substitution
        # (see support/cmake/FindSphinx.cmake) and we just use that.
        if(dir_docs_build!=dir_docs_build.strip('@')):
            # Verify that this is a python build
            if(self.is_Python_project):
                self.dir_docs_build = os.path.join(self.dir_root,"python/docs/build")
            else:
                raise("Could not set python docs build directory.")
        else:
            self.dir_docs_build = dir_docs_build

        # Extract version & release from .version file.
        try:
            with open("%s/.version"%(self.dir_root),"r") as fp_in:
                self.version = str(fp_in.readline())
        except:
            print("Project '.version' file not found.  Setting version='unset'")
            self.version='unset'
        self.release = self.version
