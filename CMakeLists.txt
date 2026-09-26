idf_component_register(SRCS "nvs_dotenv.c"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES nvs_flash)

set(partition "dotenv")

# Find dotenv file in the project directory
idf_build_get_property(project_dir PROJECT_DIR)
set(dotenv_path ${project_dir}/.env)
get_filename_component(dotenv_path_full ${dotenv_path} ABSOLUTE)

# Generate a CSV file from .env
set(csv_path_full ${CMAKE_CURRENT_BINARY_DIR}/dotenv.csv)
add_custom_target(
    nvs_dotenv_csv ALL
    COMMAND ${CMAKE_COMMAND} -DDOTENV_FILE=${dotenv_path_full} -DCSV_FILE=${csv_path_full}
            -P ${CMAKE_CURRENT_LIST_DIR}/dotenv_to_csv.cmake
    # Doesn't depend on dotenv_path_full, so that the command doesn't fail if the file doesn't exist.
    # Running the script is cheap, and the script will generate an empty CSV if the .env file doesn't exist.
    BYPRODUCTS ${csv_path_full}
    )

partition_table_get_partition_info(size "--partition-name ${partition}" "size")
partition_table_get_partition_info(offset "--partition-name ${partition}" "offset")

# nvs_create_partition_image fails the build if the partition doesn't exist,
# but the partition is optional, so check for it first.
if(NOT "${size}" OR NOT "${offset}")
    set(message "No '${partition}' partition found, not storing environment in NVS.")
    message(STATUS ${message})
else()
    # Generate the NVS partition binary, and flash it as part of 'idf.py flash'
    # or on its own using 'idf.py dotenv-flash'.
    nvs_create_partition_image(${partition} ${csv_path_full} FLASH_IN_PROJECT DEPENDS nvs_dotenv_csv)
endif()
