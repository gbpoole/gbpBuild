"""Code for parsing cmd-line arguments

Developed with the following library versions:

    python:        3.5.2
"""

# imports
import sys
import os
import optparse

class parsed_cmd(settings_in,args_in):
    """
    This class holds the processed information describing the arguments passed on the command line.
    """
    def __init__(self):
       self.settings = settings_in
       self.args     = args_in

    def extract(self,name,default=None):
        """Extract an entry from the settings list and provide a default value."""
        if (name in self.settings):
            if (self.settings[name]==None):
                return default
            else:
                return self.settings[name]
        else:
            return default

def df_option(string):
    """Return an integer or float, depending on the value in the given string.  Needed because
    fit_transform does a check on dtype and it's important to cast the input correctly."""
    try:
        return int(string)
    except ValueError:
        return float(string)

def process(argv,positional_arguments=None,optional_arguments=None,n_positional_arguments=None,perform_n_arg_check=True):
    """
    Return a 2-tuple: (settings object, args list).
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Set the number of optional arguments (ignore given
    #    value if positional_arguments is given) and
    #    check that either positional_arguments or
    #    n_positional_arguments has been defined
    if(positional_arguments!=None):
        n_positional_arguments=len(positional_arguments)
    elif(n_positional_arguments==None):
        parser.error("Either 'positional_arguments' or 'n_positional_arguments' must be specified when the CMD-line parser is called.")

    # Initialize the parser object:
    usage_string="usage: %prog [options]"
    for i_arg in range(n_positional_arguments):
       if(positional_arguments!=[]):
           usage_string+=' '+positional_arguments[i_arg]
       else:
           usage_string+=' arg%d'%(i_arg+1)
    parser = optparse.OptionParser(
        usage    =usage_string,
        formatter=optparse.TitledHelpFormatter(width=78),
        add_help_option=None)

    # Add non-positional options here
    flag_help_added=False
    if(optional_arguments!=None):
        for option_argument_i in optional_arguments:
            if(option_argument_i[2]=="store" or option_argument_i[2]=="store_true" or option_argument_i[2]=="store_false"):
                parser.add_option(option_argument_i[0],option_argument_i[1],action=option_argument_i[2],help=option_argument_i[3],
                                    type=option_argument_i[4],dest=option_argument_i[5])
            else:
                parser.add_option(option_argument_i[0],option_argument_i[1],action=option_argument_i[2],help=option_argument_i[3])
            if(option_argument_i[0]=="-h"):
                flag_help_added=True
    if(not flag_help_added):
        parser.add_option(      # customized description; put --help last
            '-h', '--help', action='help',
            help='Show this help message and exit.')

    # Perform parsing
    settings, args = parser.parse_args(argv)

    # Sanity checks: check number of arguments, verify values, etc.
    if (perform_n_arg_check and len(args)!=n_positional_arguments):
        plural_string=''
        if(n_positional_arguments>1):
           plural_string='s'
        parser.error('program expects %d command-line argument%s, '
                     '%d specified instead: "%s".' % (n_positional_arguments,plural_string,len(args),args,))

    # Return results (convert settings to a dict)
    return parsed_cmd(vars(settings), args)

