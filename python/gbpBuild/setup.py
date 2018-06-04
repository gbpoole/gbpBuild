from distutils.core import setup
from setuptools import setup, find_packages
import os
import gbpBuild.project as prj
import gbpBuild.package as pkg
import gbpBuild.log as SID

# Fetch all the meta data for the project & package
this_project = prj.project(__file__)
this_package = pkg.package(__file__)

# Print project and package meta data to stdout
SID.log.comment('')
SID.log.comment(this_project)
SID.log.comment(this_package)

# Initialize the list of package scripts with a script which can be
# run to query the build parameters, version, etc. of the package.
package_scripts = ["%s_info"%(this_package.params['name'])]

# Add aditional package scripts here
package_scripts.append("gbpBuild")
package_scripts.append("update_gbpBuild_docs")

# This line converts the package_scripts list above into the entry point 
# list needed by Click, provided that: 
#    1) each script is in its own file
#    2) the script name matches the file name
entry_points = [ "%s=%s.scripts.%s:%s"%(script_i,this_package.params['name'],script_i,script_i) for script_i in package_scripts ]

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
