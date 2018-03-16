# This file creates all the makefile targets needed for 'tests'

# Add all tests to this list
set(TESTS "")

# Add test targets 
foreach(test ${TESTS})
    add_test(NAME ${test} COMMAND ${test})
    set_target_properties(${test} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/tests")
endforeach(test)

# Configure test properties
set_target_properties(tests PROPERTIES LINKER_LANGUAGE CXX)
