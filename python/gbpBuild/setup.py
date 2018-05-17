from distutils.core import setup
from setuptools import setup, find_packages
import os
import gbpBuild.project as prj

def package_files(directory='gbpBuild/data'):
    """
    Generate a list of non-code files to be included in the package.

    By default, all files in the 'data' directory in the package root will be added.
    :param directory: The path to walk to generate the file list.
    :return: a list of filenames.
    """
    paths = []
    for (path, directories, filenames) in os.walk(directory,followlinks=True):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

# Set all the meta data for the project
project_current = prj.project()

# Print package meta data to stdout
print(project_current)

# Initialize the list of package scripts with a script which can be
# run to query the build parameters, version, etc. of the package.
package_scripts = ["%s_info"%(meta_data.package_name)]

# Add aditional package scripts here
package_scripts.append("gbpBuild")
package_scripts.append("update_gbpBuild_docs.py")

# This line converts the package_scripts list above into the entry point 
# list needed by Click provided: 
#    1) each script is in its own file
#    2) the script name matches the file name
entry_points = [ "%s=%s.scripts.%s:%s"%(script_i,meta_data.package_name,script_i,script_i) for script_i in package_scripts ]

setup(
    name=project_current.params['package_name'],
    version=project_current.params['version'],
    description=project_current.params['description'],
    author=project_current.params['author'],
    author_email=project_current.params['author_email'],
    install_requires=['Click'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    packages=find_packages(),
    entry_points={'console_scripts': entry_points},
    package_data={meta_data.package_name: package_files()},
)
