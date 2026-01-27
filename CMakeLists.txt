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
idf_build_get_property(python PYTHON)
add_custom_target(
    nvs_dotenv_csv ALL
    COMMAND ${python} ${CMAKE_CURRENT_LIST_DIR}/dotenv_to_csv.py ${dotenv_path_full} ${csv_path_full}
    # Doesn't depend on dotenv_path_full, so that the command doesn't fail if the file doesn't exist.
    # Running the script is cheap, and the script will generate an empty CSV if the .env file doesn't exist.
    BYPRODUCTS ${csv_path_full}
    )

partition_table_get_partition_info(size "--partition-name ${partition}" "size")
partition_table_get_partition_info(offset "--partition-name ${partition}" "offset")


if(NOT "${size}" OR NOT "${offset}")
    set(message "No '${partition}' partition found, not storing environment in NVS.")
    message(STATUS ${message})

else()
    # Call nvs partition generator to create an NVS partition binary
    set(image_file ${CMAKE_BINARY_DIR}/${partition}.bin)
    idf_build_get_property(idf_path IDF_PATH)
    add_custom_target(
        nvs_${partition}_bin ALL
        COMMAND ${python} ${idf_path}/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py generate --version 2 ${csv_path_full} ${image_file} ${size}
        DEPENDS ${csv_path_full} nvs_dotenv_csv
        BYPRODUCTS ${image_file}
        )

    # Flash the NVS partition binary to the device
    idf_component_get_property(main_args esptool_py FLASH_ARGS)
    idf_component_get_property(sub_args esptool_py FLASH_SUB_ARGS)
    esptool_py_flash_target(${partition}-flash "${main_args}" "${sub_args}" ALWAYS_PLAINTEXT)
    esptool_py_flash_to_partition(${partition}-flash "${partition}" "${image_file}")
    add_dependencies(${partition}-flash nvs_${partition}_bin)
    esptool_py_flash_to_partition(flash "${partition}" "${image_file}")
    add_dependencies(flash nvs_${partition}_bin)
endif()
