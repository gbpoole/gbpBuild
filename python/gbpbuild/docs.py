import os
import sys
import re
import subprocess 

def parse_cmake_local(cur_dir,search_string,result_list,active_API_module,module_select=None,module_list=None,prepend_path=True,strip_ext=False):
    # TODO: Remove external directories from files and paths
    # TODO: Remove submodules from files and paths
    with open( cur_dir + "/" + "local.cmake", 'r') as infile:
        for line in infile:
            line=line.strip()
            if(len(line)>0):
                if(line[0] != '#'):
                    # Remove '()'s and '"'s and split into words
                    words = line.replace('('," ").replace(')'," ").replace('"'," ").split()
                    # If this is an append line, then we have an item to keep
                    if(words[1].strip() == "APPEND" and len(words)==4):
                        if(words[2].strip()==search_string):
                            item = words[3].strip()
                            # If we've asked to strip extensions, do so
                            if(strip_ext):
                                item=os.path.splitext(item)[0]
                            # If we've asked to prepend paths, do so
                            if(prepend_path):
                                item=cur_dir + '/' + item
                            # Append to the result
                            if(module_select == None or (module_select != None and active_API_module[0]==module_select)):
                                result_list.append(item)
                                if(module_list != None):
                                    module_list.append(active_API_module.copy())
                # Else we may have a Doxygen module directive.  Check for it
                else:
                    words = line[1:].strip().split()
                    if(len(words)>2):
                        words = line[1:].strip().split(None,2)
                        if(words[0].strip() == 'set_active_API_module'):
                            active_API_module[0] = words[1].strip()
                            active_API_module[1] = words[2].strip()

def parse_cmake_project(cur_dir,search_string,result_list,active_API_module=["undefined","undefined"],module_list=None,module_select=None,prepend_path=True,strip_ext=False):
    # Add local entries to list
    parse_cmake_local(cur_dir,search_string,result_list,active_API_module,module_list=module_list,module_select=module_select,prepend_path=prepend_path,strip_ext=strip_ext)

    # Build list of local project directories
    local_dirs = []
    parse_cmake_local(cur_dir,"SRCDIRS",local_dirs,active_API_module)
    parse_cmake_local(cur_dir,"PASSDIRS",local_dirs,active_API_module)

    # Recurse over local project directories
    for local_dir in local_dirs:
        if (os.path.isdir(local_dir) == True):
            parse_cmake_project(local_dir,search_string,result_list,active_API_module=active_API_module,module_list=module_list,module_select=module_select,prepend_path=prepend_path,strip_ext=strip_ext)

def harvest_doxygen_groups(file_list,group_list):
    # Loop over header files
    for file_i in file_list:
        with open(file_i, 'r') as infile:
            # Loop over each line in the file
            for line in infile:
                # Check for a Doygren comment and return its starting position (if there is one)
                comment_start=line.find("//!")
                if comment_start>=0:
                    # Check for a group definition
                    group_start=line.find("\\defgroup",comment_start+3)
                    if(group_start>0):
                        # Add the definition name to the list
                        words=line[group_start:].strip().split(None,2)
                        group_list.append([words[1],words[2]])

def write_group_to_file(project,outFile,group_to_write):
    outFile.write(".. doxygengroup:: "+group_to_write+"\n")
    outFile.write("   :project: "+project.name+"\n")
    outFile.write("   :content-only:\n")
    outFile.write("   :members:\n\n")

def cat_project_file(project,filename_root,filename_modifier,outFile,default_text=None):
    filename_in = project.dir_docs+"/"+filename_root+'.rst'+filename_modifier
    if(os.path.isfile(filename_in)):
        with open(filename_in,'r') as inFile:
            for line in inFile :
                outFile.write(line)
    elif(default_text!=None):
        outFile.write(default_text)

def underlined_text(text_to_underline,underline_character):
    if(text_to_underline != None):
        return(text_to_underline+"\n"+underline_character*len(text_to_underline)+"\n")
    else:
        return("")

def make_module_list_unique(modules_in):
    modules_out = modules_in[:]
    # This is a dumb n^2 algorithm.  Fix it!
    del_list = []
    for [i_module,module_i] in enumerate(modules_in):
        for [j_module,module_j] in enumerate(modules_in[i_module+1:]):
            if(module_i[0]==module_j[0]):
                i_del=i_module+1+j_module
                if(i_del not in del_list):
                    del_list.append(i_del)
    del_list.sort(reverse=True)
    for i_del in del_list:
        del(modules_out[i_del])
    return(modules_out)

def generate_C_API_rst(project):
    filename_root="C_API"

    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    # Generate a list of the project's header files (and their modules)
    header_file_list = []
    module_list      = []
    parse_cmake_project(project.dir_root,"INCFILES", header_file_list,module_list=module_list,prepend_path=True,strip_ext=False)
    module_list=make_module_list_unique(module_list)

    # Generate a list of doxygen groups in those header files
    group_list = []
    harvest_doxygen_groups(header_file_list,group_list)

    # copy header to output file
    cat_project_file(project,filename_root,".header",outFile,default_text=underlined_text("API Documentation",'='))

    # ----------- Output logic for this file starts here -----------

    # Loop over the modules, adding each in turn to the API docs
    for module_i in module_list:
        flag_write_header = True

        # 1) ... add this module's classes group ...
        module_group = module_i[0]+"_classes"
        group_found = group_list[group_list[:][0].index(module_group)] if module_group in group_list[:][0] else None
        if(group_found != None):
            # Add the header if there is material for this module
            if(flag_write_header):
                cat_project_file(project,filename_root,'.'+module_i[0]+".header",outFile,default_text=underlined_text(module_i[1],'-'))
                outFile.write("\n")
                flag_write_header=False
            outFile.write(group_found[1]+"\n")
            outFile.write('`'*len(group_found[1])+"\n")
            write_group_to_file(project,outFile,module_group)

        # 2) ... add this module's functions ...
        function_list=[]
        parse_cmake_project(project.dir_root,"SRCFILES", function_list, module_select=module_i[0],prepend_path=False,strip_ext=True)
        flag_write_header_group=True
        for fctn in function_list:
            # Add the header if there is material for this module
            if(flag_write_header):
                cat_project_file(project,filename_root,'.'+module_i[0]+".header",outFile,default_text=underlined_text(module_i[1],'-'))
                outFile.write("\n")
                flag_write_header=False
            if(flag_write_header_group):
                title_txt = 'Functions'
                outFile.write(title_txt+"\n")
                outFile.write('`'*len(title_txt)+"\n")
                flag_write_header_group=False
            outFile.write(".. doxygenfunction:: "+fctn+"\n")
            outFile.write("   :project: "+project.name+"\n\n")

        # 3) ... add any remaining defined groups ...
        for [group_i,group_i_desc] in group_list:
            group_words=group_i.split("_",1)
            if(len(group_words)==2):
                module_group=group_words[1]
                if(group_words[0]==module_i[0] and module_group!="classes"):
                    # Add the header if there is material for this module
                    if(flag_write_header):
                        cat_project_file(project,filename_root,'.'+module_i[0]+".header",outFile,default_text=underlined_text(module_i[1],'-'))
                        outFile.write("\n")
                        flag_write_header=False
                    outFile.write(group_i_desc+"\n")
                    outFile.write('`'*len(group_i_desc)+"\n")
                    write_group_to_file(project,outFile,group_i)

        # Add the footer if there is material for this module
        if(not flag_write_header):
            cat_project_file(project,filename_root,'.'+module_i[0]+".footer",outFile)

    # ---------------------------------------------------------------

    # copy footer to output file
    cat_project_file(project,filename_root,".footer",outFile)

    # Close output file
    outFile.close()

def reformat_Clara_help_to_rst(lines_in):
    lines_out = []
    flag_remove_top_blank_lines=True
    process_phase=0
    lines_in_split=lines_in.split('\n')
    i_opt=0
    for line in lines_in_split:
        if(len(line)>0 or not flag_remove_top_blank_lines):
            # Process usage line
            if(process_phase==0):
                words=line.split(' ')
                if(len(words)>0):
                    if(words[0]=="usage:"):
                        process_phase=1
                lines_out.append(line+'\n\n')
            # Process execution example line
            elif(process_phase==1):
                words=line.split()
                if(len(words)>0):
                    line='``'+line.strip()+'``'
                    process_phase=2
                lines_out.append(line+'\n')
            # Process "where options ..." line
            elif(process_phase==2):
                words=line.split()
                if(len(words)>0):
                    if(line=="where options are:"):
                        process_phase=3
                lines_out.append(line+'\n')
            # Process options
            elif(process_phase==3):
                words=line.split(' ')
                if(len(words)<2):
                    process_phase=4
                else:
                    n_opts=0
                    opt_searching=True
                    for i_word,word in enumerate(words):
                        if(len(word)>1):
                            if(word[0:1]=='--'):
                                if(opt_searching):
                                    words[i_word]='**'+word+'**'
                                    n_opts+=1
                            elif(word[0]=='-'):
                                if(opt_searching):
                                    words[i_word]='**'+word+'**'
                                    n_opts+=1
                            else:
                                if(word != ' '):
                                    if(opt_searching):
                                        words[i_word]='\n\t'+words[i_word]
                                    opt_searching=False
                    line=' '.join(words)
                lines_out.append(line+'\n')
            # Process everything else
            else:
                lines_out.append(line+'\n')
            flag_remove_top_blank_lines=False
    return(''.join(lines_out))

def generate_C_execs_rst(project):
    filename_root="C_execs"

    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    # Generate a list of the project's header files (and their modules)
    header_file_list   = []
    header_module_list = []
    parse_cmake_project(project.dir_root,"INCFILES", header_file_list,module_list=header_module_list,prepend_path=True,strip_ext=False)
    module_list=make_module_list_unique(header_module_list)

    # Generate a list of doxygen groups in those header files
    group_list = []
    harvest_doxygen_groups(header_file_list,group_list)

    # copy header to output file
    cat_project_file(project,filename_root,".header",outFile,default_text=underlined_text("Applications",'='))

    # ----------- Output logic for this file starts here -----------

    # Loop over the modules, adding each in turn to the API docs
    for module_i in module_list:
        exe_list=[]
        parse_cmake_project(project.dir_root,"EXEFILES", exe_list, module_select=module_i[0],prepend_path=False,strip_ext=True)
        flag_write_header=True
        for exec_i in exe_list:
            # Add the header if there is material for this module
            if(flag_write_header):
                cat_project_file(project,filename_root,'.'+module_i[0]+".header",outFile,default_text=underlined_text(module_i[1],'-'))
                outFile.write("\n")
                flag_write_header=False

            # Send output of executable to the output file
            outFile.write(exec_i+'\n')
            outFile.write('-'*len(exec_i)+'\n')
            out = subprocess.check_output(["/Users/gpoole/gbpSID/build-dev/"+exec_i, "-h"]).decode("utf-8")
            outFile.write(reformat_Clara_help_to_rst(out))

        # Add the footer if there is material for this module
        if(not flag_write_header):
            cat_project_file(project,filename_root,'.'+module_i[0]+".footer",outFile)

    # ---------------------------------------------------------------

    # copy footer to output file
    cat_project_file(project,filename_root,".footer",outFile)

    # Close output file
    outFile.close()

def generate_Python_API_rst(project):
    filename_root="Python_API"

    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    outFile.write(underlined_text("Python API",'-'))

    # Close output file
    outFile.close()


def generate_Python_execs_rst(project):
    filename_root="Python_execs"

    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    outFile.write(underlined_text("Python Executables",'-'))

    # Close output file
    outFile.close()

def generate_default_rst(project,filename_root="header",default_title=None):
    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    # copy header to output file
    cat_project_file(project,filename_root,"",outFile,default_text=underlined_text(default_title,'='))

    # Close output file
    outFile.close()

def generate_index_rst(project):
    filename_root="index"

    # Open the output file for writing
    outFile = open(project.dir_docs_build + "/" + filename_root + '.rst', "w")

    # copy header to output file
    cat_project_file(project,filename_root,".header",outFile)

    # Add a table of contents title
    outFile.write("\n")
    outFile.write("Table of Contents\n")
    outFile.write("-----------------\n")
    outFile.write("\n")

    outFile.write(".. "+project.name+" documentation master file\n")
    outFile.write("\n")
    outFile.write(".. toctree::\n")
    outFile.write("   :maxdepth: 2\n")
    outFile.write("\n")

    # Set the default document order
    doc_order = ['install.rst']
    if(project.is_C_project and project.is_Python_project):
        doc_order.append('C_execs.rst')
        doc_order.append('Python_execs.rst')
        doc_order.append('C_API.rst')
        doc_order.append('Python_API.rst')
    elif(project.is_Python_project):
        doc_order.append('Python_execs.rst')
        doc_order.append('Python_API.rst')
    elif(project.is_C_project):
        doc_order.append('C_execs.rst')
        doc_order.append('C_API.rst')

    # Check if there is a 'doc_order.txt' file and over-write the defaults with it if so
    filename_in = project.dir_docs+"/index_order.txt"
    if(os.path.isfile(filename_in)):
        with open(filename_in,"r") as inFile:
            doc_order = []
            for line in inFile:
                doc_order.append(line)

    for doc_i in doc_order:
        outFile.write("   "+doc_i+"\n")

    outFile.write("\n")
    outFile.write("* :ref:`genindex`\n")

    # copy header to output file
    cat_project_file(project,filename_root,".footer",outFile)

    # Close output file
    outFile.close()

