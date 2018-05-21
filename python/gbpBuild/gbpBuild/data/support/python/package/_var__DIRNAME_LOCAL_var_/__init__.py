import os

# Return the full path to a file in the package's data directory
_PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),'../'))
def full_path_datafile(path):
    """
    Return the full *INSTALLED* path to a directory in the package's root directory.
    :param path: A path relative to the package root directory
    :return: The installed path
    """
    return os.path.join(_PACKAGE_ROOT, 'data', path)
