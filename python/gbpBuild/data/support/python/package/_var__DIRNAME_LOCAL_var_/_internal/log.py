"""This module provides a `log_stream` class for generating logging
information.  It is intended for the generation of course-grained reporting of
program execution for the user and should not be used in performance-critical
situations, in tight loops, etc.

Formatting is organized by indenting levels which can be
increased/decreased by calling the open/close methods of the stream
respectively.
"""
# For legacy-Python compatibility
from __future__ import print_function

import os
import sys
import importlib
import time
import datetime

# Infer the name of this package from the path of __file__
package_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
package_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
package_name = os.path.basename(package_root_dir)

# Make sure that what's in this path takes precedence
# over an installed version of the project
sys.path.insert(0, package_parent_dir)

# Import needed internal modules
_internal = importlib.import_module(package_name + '._internal')

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def format_time(seconds, granularity=None):
    """Create a nice ASCII representation of a time interval, given in seconds.

    :param seconds: Time in seconds
    :param granularity: The maximum number of interval levels to report
    :return: string
    """
    result = []

    for i_interval, [name, count] in enumerate(intervals):
        value = seconds // count
        if value:
            seconds -= value * count
            if(name == intervals[-1][0] or i_interval == granularity):
                result.append("%.1f %s" % (value, name))
            else:
                if value == 1:
                    name = name.rstrip('s')
                result.append("%d %s" % (value, name))

    if(granularity):
        result = ', '.join(result[:granularity])
    else:
        result = ', '.join(result)

    # Replace the last ',' with 'and'
    result_split = result.rsplit(',', 1)
    if(len(result_split) > 1):
        result = ' and'.join(result_split)

    return result


class log_stream(object):
    """This class provides a file pointer for logging user feedback and methods
    for writing to it."""

    def __init__(self, fp_out=None,verbosity=True,n_indent_max=10):
        """Generate an instance of the log_stream class.

        :param fp_out: An optional file pointer to use for the log.
        :param verbosity: An optional parameter that sets the default verbosity of the stream.
        """
        # File pointer where the stream will write to
        self.set_fp(fp_out)

        # Number of spaces to indent for each indent-level
        self.indent_size = 3

        # Set the maximum number of indent levels to render
        self.n_indent_max = n_indent_max

        # These lists will have one entry per indent-level
        self.t_last = [time.time()]
        self.n_lines = [0]
        self.splice = [None]

        # This list will be a stack with one entry per verbosity state.  Initialize with the given default.
        self.verbosity = []
        self.verbosity_default = verbosity
        self.set_verbosity(self.verbosity_default)

        # Indicates whether the last-written line
        # ended with a new line
        self.hanging = False

    def set_fp(self, fp_out=None):
        """Set the file pointer to be used for logging.  Default is
        `sys.stderr`.

        :param fp_out: File pointer
        :return: None
        """
        if(fp_out is None):
            self.fp = sys.stderr
        else:
            self.fp = fp_out

    def set_verbosity(self,verbosity=True):
        """
        Add a new (and make it current) verbosity state to the stream's stack of verbosity states.

        This method takes either a boolean flag indicating whether logging is active, or an integer indicating
        the maximum indenting level that will be rendered.  It can be removed using the
        :py:meth:`~.log.log_stream.unset_verbosity` method.  See the
        :py:meth:`~.log.log_stream.check_verbosity` method for an account of how the verbosity passed to this
        method is interpreted.

        :param verbosity: A boolean flag indicating if logging is active, or an integer indicating the verbosity level
        :return: None
        """

        # Check validity of the given verbosity
        if(not isinstance(verbosity,(bool,int))):
            self.error("Invalid datatype {%s} being added to log stream's verbosity state."%(type(verbosity)))

        # Add a state to the stack
        self.verbosity.append(verbosity)

    def unset_verbosity(self):
        """
        Revert stream to a previous verbosity state if one exists; the default state otherwise.

        :return: None
        """
        if(len(self.verbosity)>0):
            self.verbosity.pop()

    def verbosity_level(self,verbosity):
        """
        Convert a verbosity state value to a corresponding verbosity level.

        :param verbosity: Verbosity state value
        :return: Integer indent level
        """

        # Default result
        result = self.n_indent_max

        # If state is a bool and evaluates to false, return -1 (i.e. a value always > self._n_indent()
        if (isinstance(verbosity, bool)):
            if(not verbosity):
                result = -1

        # ... else, if it's an integer, return it or n_indent_max
        elif (isinstance(verbosity,int)):
            result = max([verbosity,self.n_indent_max])

        # ... else, unsupported data type ... throw an error
        else:
            self.error("Can not interpret verbosity level of a verbosity state with unsupported type {%s}."%(type(verbosity)))

        return result

    def check_verbosity(self):
        """
        Check if the stream is active.

        :return: A boolean indicating if rendering is active on the stream
        """

        # If the verbosity stack is empty, use the default
        if(len(self.verbosity)<1):
            max_active_level = self.verbosity_level(self.verbosity_default)
        else:
            max_active_level = self.n_indent_max
            for state in self.verbosity:
                max_active_level = min([max_active_level,self.verbosity_level(state)])

        return max_active_level>=self._n_indent()


    def open(self, msg, splice=None):
        """Open a new indent bracket for the log.

        :param msg: An object with a __str__ method, or a list thereof
        :return: None
        """
        self._print(msg, unhang=True, indent=True)
        self.t_last.append(time.time())
        self.n_lines.append(0)
        self.splice.append(splice)
        if(splice):
            self._splice_line(splice, True)

    def close(self, msg=None, time_elapsed=False):
        """Close a new indent bracket for the log.

        Add an elapsed time since the last open to the end if time_elapsed=True

        :param msg: An object with a __str__ method, or a list thereof
        :param time_elapsed: Boolean flag indicating whether to report the time elapsed for this indent level
        :return: None
        """

        # Sanity checks
        if(self._n_indent() < 1):
            self.error("Invalid log closure.")

        # Decrement the indent level and fetch the info about the level we are closing
        t_last = self.t_last.pop()
        n_lines = self.n_lines.pop()
        splice = self.splice.pop()

        # This must be called every time because we need the
        # pop on t_last to keep track of the indenting level
        dt = time.time() - t_last

        if(splice):
            self._splice_line(splice, False)

        # Generate message
        if(msg is not None):
            if(time_elapsed):
                msg_time = " (%s)" % (format_time(dt))
            else:
                msg_time = ''
            self._print(msg + msg_time, unhang=(n_lines > 1))
        self._unhang()

    def comment(self, msg, unhang=True, overwrite=False, blankline_before=False, blankline_after=False):
        """Add a one-line comment to the log.

        :param msg: An object with a __str__ method, or a list thereof
        :param unhang:
        :param overwrite:
        :return: None
        """
        if(blankline_before):
            self.blankline()
        self._print(msg, unhang=unhang, indent=True, overwrite=overwrite)
        if(blankline_after):
            self.blankline()

    def append(self, msg):
        """Add to the end of the current line in the log.

        :param msg: An object with a __str__ method, or a list thereof
        :return: None
        """
        self._print(msg, unhang=False, indent=False)

    def progress_bar(self, gen, count, *args, **kwargs):
        """Display a progress bar for a generator.

        :param gen: Generator
        :param count: Number of generator iterations
        :param args: Positional arguments to pass to the generator
        :param kwargs: Keyword arguments to pass to the generator
        :return: None
        """

        # Initialize counter
        width = 30
        msg_len_last = 0
        start_time = time.time()
        self.comment("[%s] Remaining:" % (' ' * width), unhang=True)

        # Iterate
        for iteration, result in enumerate(gen(*args, **kwargs)):
            fraction_complete = float(iteration + 1) / float(count)
            ticks = int(fraction_complete * float(width + 1))
            secs_elapsed = time.time() - start_time
            secs_estimate = int(secs_elapsed / fraction_complete)
            secs_remaining = secs_estimate - secs_elapsed
            if(secs_remaining > 0):
                msg = "[%s%s] Remaining: %s" % ('#' * ticks, ' ' * (width - ticks),
                                                str(datetime.timedelta(seconds=secs_remaining)).split('.')[0])
                msg_len = len(msg)

                # Make sure to blank-out any old underlying text
                if(msg_len < msg_len_last):
                    msg += ' ' * (msg_len_last - msg_len)
                msg_len_last = msg_len
                self.comment(msg, unhang=False, overwrite=True)

        # Finalize counter
        msg = "[%s%s] Time elapsed: %s" % ('#' * ticks, ' ' * (width - ticks),
                                           str(datetime.timedelta(seconds=secs_elapsed)).split('.')[0])
        msg_len = len(msg)
        if(msg_len < msg_len_last):
            msg += ' ' * (msg_len_last - msg_len)
        self.comment(msg, unhang=False, overwrite=True)

    def error(self, err_msg, code=None):
        """Raise an exception.

        :param err_msg: Error message
        :param code: Optional error code to report
        :return: None
        """
        self._unhang()
        if(code):
            message = err_msg + " [code=" + code + "]"
        else:
            message = err_msg
        raise Exception(message)

    def blankline(self):
        """Print a blank line to the stream.

        :return: None
        """
        self.comment('\n', unhang=True)

    def raw(self, msg):
        """Print raw, unformatted text to the log.

        :param msg: An object with a __str__ method, or a list thereof
        :return: None
        """
        self._print(msg, unhang=True, indent=False)

    def _splice_line(self, splice_msg, flag_start):
        """Create splice lines in the log for isolating sections of the stream.

        This method is intended to be used when uncontrolled output from other sources are polluting the stream.  Open an indentation
        block around cases like this using the splice keyword argument, and a clearly identifiable line will be
        rendered at the start and end of the section.

        :param splice_msg:
        :param flag_start:
        :return:
        """
        n_splice = 40
        n_lead_min = 10
        lead_char = '='
        msg = ' ' + splice_msg + ' - '
        if (flag_start):
            msg += 'start '
        else:
            msg += 'end '
        n_msg = len(msg)
        n_lead = int((n_splice - len(msg)) / 2)
        if (n_lead <= 0):
            n_splice = n_msg + 2 * n_lead_min
            n_lead = n_lead_min
            n_tail = n_lead_min
        else:
            n_tail = n_splice - n_msg - n_lead
        self._print(n_lead * lead_char + msg + n_tail * lead_char + '\n', unhang=True, indent=False)

    def _print(self, msg, unhang=True, indent=True, overwrite=False, iterables_allowed=True, **kwargs):
        """This method is the main driver of output to the stream, but should
        be accessed through other methods.

        :param msg: An object with a __str__ method, or a list thereof
        :param unhang: Boolean flag indicating whether to start with a carriage return
        :param indent: Boolean flag indicating whether to start the line with an indent
        :param iterables_allowed: Boolean flag indicating whether to accept an iterable msg
        :param kwargs: keyword arguments to be passed to the print function
        :return: None
        """
        # Check if rendering is active on the stream
        if(self.check_verbosity()):

            # Optionally unhang the stream
            if(unhang):
                self._unhang()

            # This will fail for strings but pass for lists, etc.
            if(_internal.is_nonstring_iterable(msg)):
                if(overwrite):
                    self.error("Log stream overwriting not permitted for iterables.")
                if(not iterables_allowed):
                    self.error("An iterable was passed to a log stream method which does not accept them.")
                for line in msg:
                    self._print(line, indent=indent, overwrite=overwrite, **kwargs)
            # ... render a non-iterable object ...
            else:
                # If msg is a string (or converts to one) with newline characters, break-it-up
                # and recall this method with the result to treat it as an iterable
                msg_split = str(msg).splitlines(True)
                if(len(msg_split) > 1):
                    self._print(msg_split, indent=indent, overwrite=overwrite,
                                iterables_allowed=iterables_allowed, **kwargs)
                # ... else, render a single line
                else:
                    if(not self.hanging and len(msg) > 0):
                        self.n_lines[-1] += 1
                    if(overwrite or (not self.hanging and indent)):
                        self._indent(overwrite=overwrite)
                    print(msg, end='', file=self.fp, **kwargs)
                    self.fp.flush()
                    if(msg.endswith('\n')):
                        self.hanging = False
                    else:
                        self.hanging = True

    def _unhang(self):
        """If the log did not previously end with a newline, add one.

        :return: None
        """
        if(self.hanging):
            print ('', file=self.fp)
            self.n_lines[-1] += 1
            self.hanging = False

    def _indent(self, overwrite=False):
        """Write the appropriate indent for this line (with an option to
        overwrite)

        :param overwrite: Boolean flag indicating whether to overwrite the current line
        :return: None
        """
        if(overwrite):
            print ('\r', end='', file=self.fp)
        print (self.indent_size * self._n_indent() * ' ', end='', file=self.fp)

    def _n_indent(self):
        """Return the current indent level of the stream.

        :return: Integer
        """
        return len(self.t_last) - 1
