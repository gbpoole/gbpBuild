#========= Set project-specific options ========
# eg. option(SID_DEBUG "Enable SID debugging information" OFF)

#=========== Add 3rd-party libraries ===========
# (look in gbpBuild/cmake/3rd_party.cmake for a list of supported libraries)
message(STATUS "")
message(STATUS "Initializing 3rd-party libraries...")

# The following three macros have been set-up for automating 
# 3rd-party library configuration  The folling libraries are
# supported at the moment:
#    - GBP_DOCS_BUILD
#    - MPI
#    - MPI_IO
#    - CUDA
#    - CUFFT
#    - GD
#    - CFITSIO
#    - HDF5
#    - FFTW
#    - OpenMP
#
# List the following (one-per line):

# 1) *required* 3rd-Party libraries. 
#
# First & only argument is library name.
#
# The build will fail if any of these fail to be configured.
#set_3rd_party_required("XXX")

# 2) *requested* 3rd-Party libraries (and their defaults).
#
# First argument is library name; second is default state (ON or OFF).
#
# The build will proceed if these fail to configure.
#set_3rd_party_requested("XXX" ON)

# 3) *optional* 3rd-Party libraries (and their defaults).
#
# First argument is library name; second is default state (ON or OFF).
#
# The build will succeed if any of these are switched off but
# will fail if they are turned on and fail to configure.
#set_3rd_party_optional("XXX" ON)

# Print status message
message(STATUS "Finished initializing 3rd-party libraries.")
