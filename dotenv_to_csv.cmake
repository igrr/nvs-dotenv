# SPDX-FileCopyrightText: 2026 Ivan Grokhotkov
# SPDX-License-Identifier: Apache-2.0
#
# Converts a .env file into a CSV file for the NVS partition generator.
#
# Usage:
#   cmake -DDOTENV_FILE=<path of input .env file> -DCSV_FILE=<path of output .csv file> -P dotenv_to_csv.cmake
#
# The .env file consists of VAR_NAME=value lines. Empty lines and lines starting
# with '#' are ignored. Whitespace around the name and the value is removed,
# and so are double quotes around the value. If the .env file doesn't exist,
# a CSV file with no variables is written.
#
# The CSV file is only written if its contents change, so that the NVS
# partition isn't regenerated when nothing has changed.

cmake_minimum_required(VERSION 3.16)

if(NOT DEFINED DOTENV_FILE OR NOT DEFINED CSV_FILE)
    message(FATAL_ERROR "Usage: cmake -DDOTENV_FILE=<.env file> -DCSV_FILE=<.csv file> -P dotenv_to_csv.cmake")
endif()

# Quote a field the way Python's csv.writer does by default (QUOTE_MINIMAL):
# nvs_partition_gen.py reads the file with csv.DictReader, and would otherwise
# truncate a value containing a comma.
function(csv_field value out_var)
    if("${value}" MATCHES "[,\"\r\n]")
        string(REPLACE "\"" "\"\"" value "${value}")
        set(value "\"${value}\"")
    endif()
    set(${out_var} "${value}" PARENT_SCOPE)
endfunction()

message(NOTICE "Processing dotenv file (${DOTENV_FILE})")

# Variables are stored as var_name_<i> and var_value_<i>, rather than as a
# CMake list, since names and values may contain semicolons.
#
# Strings from the .env file are assigned using string(CONCAT) rather than
# set(), since set() treats a value of PARENT_SCOPE or CACHE as a keyword.
set(var_count 0)

if(NOT EXISTS "${DOTENV_FILE}")
    message(NOTICE "Dotenv file (${DOTENV_FILE}) not found, no environment variables will be saved in NVS")
    set(contents "")
else()
    file(READ "${DOTENV_FILE}" contents)
    # Accept CRLF and CR line endings, same as Python's universal newlines mode
    string(REPLACE "\r\n" "\n" contents "${contents}")
    string(REPLACE "\r" "\n" contents "${contents}")
endif()

# Go through the file line by line. file(STRINGS) and list operations aren't
# used here, since they would split the lines on semicolons.
set(lineno 0)
while(NOT "${contents}" STREQUAL "")
    math(EXPR lineno "${lineno} + 1")
    string(FIND "${contents}" "\n" eol)
    if(eol EQUAL -1)
        string(CONCAT line "${contents}")
        set(contents "")
    else()
        string(SUBSTRING "${contents}" 0 ${eol} line)
        math(EXPR eol "${eol} + 1")
        string(SUBSTRING "${contents}" ${eol} -1 contents)
    endif()

    # ignore empty lines and comments
    string(STRIP "${line}" line)
    if("${line}" STREQUAL "" OR "${line}" MATCHES "^#")
        continue()
    endif()

    # The line should be in format VAR_NAME=value, value may be quoted
    string(FIND "${line}" "=" eq)
    if(eq EQUAL -1)
        message(FATAL_ERROR "${DOTENV_FILE}: line ${lineno}: expected VAR_NAME=value, got '${line}'")
    endif()
    string(SUBSTRING "${line}" 0 ${eq} name)
    math(EXPR eq "${eq} + 1")
    string(SUBSTRING "${line}" ${eq} -1 value)
    string(STRIP "${name}" name)
    string(STRIP "${value}" value)
    string(REGEX REPLACE "^\"+" "" value "${value}")
    string(REGEX REPLACE "\"+$" "" value "${value}")
    # We could try to add variable interpolation here

    # If a variable is defined more than once, the last value wins, but the
    # variable keeps the position where it was first defined.
    set(index ${var_count})
    if(var_count GREATER 0)
        math(EXPR last "${var_count} - 1")
        foreach(i RANGE ${last})
            if("${var_name_${i}}" STREQUAL "${name}")
                set(index ${i})
                break()
            endif()
        endforeach()
    endif()
    if(index EQUAL var_count)
        math(EXPR var_count "${var_count} + 1")
    endif()
    string(CONCAT var_name_${index} "${name}")
    string(CONCAT var_value_${index} "${value}")
endwhile()

# prepare the CSV file for NVS partition generator.
set(csv "key,type,encoding,value\n")
# write namespace entry
string(APPEND csv "dotenv,namespace,,\n")
if(var_count GREATER 0)
    math(EXPR last "${var_count} - 1")
    foreach(i RANGE ${last})
        csv_field("${var_name_${i}}" name)
        csv_field("${var_value_${i}}" value)
        string(APPEND csv "k${i},data,string,${name}\n")
        string(APPEND csv "v${i},data,binary,${value}\n")
    endforeach()
endif()
string(APPEND csv "count,data,u32,${var_count}\n")

# Don't update the resulting file if no changes are required
if(EXISTS "${CSV_FILE}")
    file(READ "${CSV_FILE}" old_csv)
    if("${old_csv}" STREQUAL "${csv}")
        return()
    endif()
endif()
file(WRITE "${CSV_FILE}" "${csv}")
