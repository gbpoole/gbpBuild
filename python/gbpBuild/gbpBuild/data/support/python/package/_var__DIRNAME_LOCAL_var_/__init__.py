import os

_PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
def full_path_datafile(path):
    """
    Return the full *INSTALLED* path to a directory in the package's root directory.
    :param path: A path relative to the package root directory
    :return: The installed path
    """
    return os.path.join(_PACKAGE_ROOT, 'data', path)

def import_packages():
    """
    Import all the python packages belonging to this project.
    """
    dir_file = os.path.abspath(__file__)
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
