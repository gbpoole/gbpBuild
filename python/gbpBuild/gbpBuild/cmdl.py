"""Code for parsing cmd-line arguments.

This code has been rendered obsolete by Click.  Kept for legacy reasons.
"""

import optparse
import os
import sys
import gbpBuild


class parser:
    """This class holds the processed information describing the arguments
    passed on the command line."""

    def __init__(self, argv, positional_arguments=None, optional_arguments=None, n_positional_arguments=None):
        """Parser constructor `argv` is a list of arguments, or `None` for
        ``sys.argv[1:]``.

        positional_arguments is a list of 2-element lists.  For each:
            element[0]: is the argument name
            element[1]: is the default value
        optional_arguments is a list of 5-element lists.  For each:
            element[0]: list of opt_strs (len() must be >0)
            element[1]: help text
            element[2]: storage type
            element[3]: default value
            element[4]: storage destination
        n_positional_arguments can be specified instead of positional_arguments
        to initialize a set of n_positional_arguments generic required arguments instead
        Positional arguments with default=None are required
        Optional positional arguments will be assigned values in the order they are given

        """
        if argv is None:
            argv = sys.argv[1:]

        # Set the number of optional arguments (ignore given
        #    value if positional_arguments is given) and
        #    check that either positional_arguments or
        #    n_positional_arguments has been defined
        if(positional_arguments is not None):
            if(n_positional_arguments is not None):
                parser.error(
                    "Either 'positional_arguments' or 'n_positional_arguments' (but not both) must be specified when the CMD-line parser is called.")
        elif(n_positional_arguments is None):
            parser.error(
                "Either 'positional_arguments' or 'n_positional_arguments' (but not both) must be specified when the CMD-line parser is called.")

        # If positional_arguments has not been specified, create it (make them all required)
        if(positional_arguments is None):
            positional_arguments = []
            for i_arg in range(n_positional_arguments):
                positional_arguments.append(['arg%d' % (i_arg + 1), None])
        else:
            n_positional_arguments = len(positional_arguments)

        # Separate and count the required positional arguments from the optional ones
        required_positional_arguments = [p_i for p_i in positional_arguments if(p_i[1] is None)]
        optional_positional_arguments = [p_i for p_i in positional_arguments if(p_i[1] is not None)]
        n_required_positional_arguments = len(required_positional_arguments)
        n_optional_positional_arguments = len(optional_positional_arguments)

        # Initialize the parser usage string
        usage_string = "usage: %prog"
        for [positional_arguments_type, arg_vers_txt_1, arg_vers_txt_2] in [
                [required_positional_arguments, '', ''], [optional_positional_arguments, '<', '>']]:
            for positional_argument_i in positional_arguments_type:
                usage_string += ' ' + arg_vers_txt_1 + positional_argument_i[0] + arg_vers_txt_2
        usage_string += " options"
        parser = optparse.OptionParser(
            usage=usage_string,
            # formatter=optparse.TitledHelpFormatter(width=78),
            formatter=optparse.IndentedHelpFormatter(width=100),
            add_help_option=None)

        # Add non-positional options here
        flag_help_added = False
        if(optional_arguments is not None):
            for option_argument_i in optional_arguments:
                opt_strings = option_argument_i[0]
                opt_help_txt = option_argument_i[1]
                opt_dtype = option_argument_i[2]
                opt_default = option_argument_i[3]
                opt_dest = option_argument_i[4]
                opt_action = 'store'
                if(opt_dtype == 'bool'):
                    if(opt_default):
                        opt_action = 'store_false'
                    elif(opt_default == False):
                        opt_action = 'store_true'
                    else:
                        parser.error('Invalid default (%s) for boolean option (%s).' % (opt_default, opt_dest))
                    parser.add_option(*opt_strings, action=opt_action, help=opt_help_txt, dest=opt_dest)
                else:
                    parser.add_option(*opt_strings, action=opt_action, help=opt_help_txt, type=opt_dtype, dest=opt_dest)
                if(option_argument_i[0] == "-h"):
                    flag_help_added = True

        # Add help to the list of options
        if(not flag_help_added):
            parser.add_option(      # customized description; put --help last
                '-?', '-h', '--help', action='help',
                help='display usage information')

        # Perform parsing
        settings, args = parser.parse_args(argv)
        n_args = len(args)

        # Sanity checks: check number of arguments
        if (len(args) < n_required_positional_arguments):
            plural_string1 = ''
            if(n_positional_arguments > 1):
                plural_string1 = 's'
            plural_string2 = 'was'
            if(n_args > 1):
                plural_string2 = 'were'
            parser.error('program expects at least %d command-line argument%s.  ' '%d %s given instead: "%s".' %
                         (n_required_positional_arguments, plural_string1, len(args), plural_string2, args,))
        elif (len(args) > n_positional_arguments):
            plural_string1 = ''
            if(n_positional_arguments > 1):
                plural_string1 = 's'
            plural_string2 = 'was'
            if(n_args > 1):
                plural_string2 = 'were'
            parser.error(
                'program expects no more than %d command-line argument%s.  '
                '%d %s given instead: "%s".' %
                (n_required_positional_arguments, plural_string1, len(args), plural_string2, args,))

        # Ensure that settings is a dictionary
        self.settings = vars(settings)

        # Apply defaults to optional arguments
        for optional_argument_i in optional_arguments:
            opt_key = optional_argument_i[4]
            opt_val = optional_argument_i[3]
            if(self.settings[opt_key] is None):
                self.settings[opt_key] = opt_val

        # Append command-line arguments to settings
        for i_arg in range(n_positional_arguments):
            # Get option index from required or optional list
            if(i_arg < n_required_positional_arguments):
                i_key = i_arg
                argument_list = required_positional_arguments
            else:
                i_key = i_arg - n_required_positional_arguments
                argument_list = optional_positional_arguments

            # Get option key and default value
            arg_key = argument_list[i_key][0]
            arg_val_default = argument_list[i_key][1]

            # Set option value to parsed value or default
            if(i_arg < n_args):
                arg_val = args[i_arg]
            else:
                arg_val = arg_val_default

            # Finally, add positional argument
            self.settings[arg_key] = arg_val

    def extract(self, name):
        """Extract an entry from the settings list and provide a default
        value."""
        try:
            rval = self.settings[name]
        except KeyError:
            gbpBuild.log.error('"%s" is not a valid command-line option.' % name)
        return rval


def df_option(string):
    """Return an integer or float, depending on the value in the given string.

    Needed because fit_transform does a check on dtype and it's
    important to cast the input correctly.
    """
    try:
        return int(string)
    except ValueError:
        return float(string)
