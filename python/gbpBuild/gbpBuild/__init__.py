import os

# Return the full path to a file in the package's data directory
_ROOT = os.path.abspath(os.path.dirname(__file__))
def full_path_datafile(path):
    return os.path.join(_ROOT, 'data', path)

