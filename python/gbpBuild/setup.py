import sys
import os

# Make sure that what's in this path takes precidence
# over an installed version of the project
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

# Make sure the packages in the .requirements_dev.txt 
# project file have been installed to make sure this
# package is available.
import gbpBuild.project as prj
import gbpBuild.package as pkg
import gbpBuild.log as SID

from setuptools import setup, find_packages

def get_package_scripts(package_name):
    """
    Check the package 'scripts' directory for a list of package script files.
    """
    dir_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),package_name,"scripts")
    script_list=[]
    for (directory, directories, filenames) in os.walk(dir_file):
        if(os.path.basename(directory) != "__pycache__"):
            for filename in filenames:
                # Exclude gbpBuild (load it independently) for the case
                # that we're running this within that package.
                filename_split=os.path.splitext(filename)
                if(filename_split[0]!="__init__" and filename_split[1]==".py"):
                    script_list.append(filename_split[0])
    return script_list

# Fetch all the meta data for the project & package
this_project = prj.project(__file__)
this_package = pkg.package(__file__)

# Print project and package meta data to stdout
SID.log.comment('')
SID.log.comment(this_project)
SID.log.comment(this_package)

# This line converts a list of package_scripts harvested
# from the 'scripts' directory into the entry point 
# list needed by Click, provided that: 
#    1) each script is in its own file
#    2) there is only one entry point per script
#    3) the script name matches the file name
package_scripts=get_package_scripts(this_package.params['name'])
entry_points = [ "%s=%s.scripts.%s:%s"%(script_i,this_package.params['name'],script_i,script_i) for script_i in package_scripts ]

# Report the list of Click executables to be generated
if(len(package_scripts)>0):
    SID.log.open("The following Click entry-points will be created:")
    for script in package_scripts:
        SID.log.comment(script)
else:
    SID.log.open("No Click entry-points will be created.")
SID.log.close(None)    
SID.log.comment('')    

# Perform the set-up action
SID.log.comment("Running setup.py...")    
setup(
    name=this_package.params['name'],
    version=this_project.params['version'],
    description=this_package.params['description'],
    author=this_project.params['author'],
    author_email=this_project.params['author_email'],
    install_requires=['Click'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    packages=find_packages(),
    entry_points={'console_scripts': entry_points},
    package_data={this_package.params['name']: this_package.package_files},
)
SID.log.comment("Success.")    
