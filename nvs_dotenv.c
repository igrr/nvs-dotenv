#include <stdio.h>
#include "nvs_dotenv.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "esp_check.h"

#define DOTENV_NVS_PARTITION "dotenv"
#define DOTENV_NVS_NAMESPACE "dotenv"
#define DOTENV_COUNT_KEY     "count"

static const char *TAG = "nvs-dotenv";

esp_err_t nvs_dotenv_load(void)
{
    nvs_handle_t nvs_handle = 0;
    char *env_name = NULL;
    char *value = NULL;
    esp_err_t ret;

    ret = nvs_flash_init_partition(DOTENV_NVS_PARTITION);
    ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to initialize NVS partition '" DOTENV_NVS_PARTITION "'");

    ret = nvs_open_from_partition(DOTENV_NVS_PARTITION, DOTENV_NVS_NAMESPACE, NVS_READONLY, &nvs_handle);
    ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to open NVS namespace");

    uint32_t env_count = 0;
    ret = nvs_get_u32(nvs_handle, DOTENV_COUNT_KEY, &env_count);
    ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed get the number of env vars");

    for (size_t i = 0; i < env_count; i++) {
        char key[NVS_KEY_NAME_MAX_SIZE];
        snprintf(key, sizeof(key), "k%d", i);

        size_t env_name_size = 0;
        ret = nvs_get_str(nvs_handle, key, NULL, &env_name_size);
        ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to get the size of env var name (key=%s)", key);
        env_name = (char *) malloc(env_name_size);
        ESP_GOTO_ON_FALSE(env_name, ESP_ERR_NO_MEM, out, TAG, "Failed to allocate %d bytes for env var name (key=%s)", env_name_size, key);
        ret = nvs_get_str(nvs_handle, key, env_name, &env_name_size);
        ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to get the env var name (key=%s)", key);

        snprintf(key, sizeof(key), "v%d", i);
        size_t value_size = 0;
        ret = nvs_get_blob(nvs_handle, key, NULL, &value_size);
        ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to get the size of env var value (key=%s)", key);
        value = (char *) malloc(value_size + 1);
        ESP_GOTO_ON_FALSE(env_name, ESP_ERR_NO_MEM, out, TAG, "Failed to allocate %d bytes for env var value (key=%s)", value_size, key);
        ret = nvs_get_blob(nvs_handle, key, value, &value_size);
        ESP_GOTO_ON_ERROR(ret, out, TAG, "Failed to get the env var value (key=%s)", key);
        value[value_size] = '\0';

        setenv(env_name, value, 1);
        free(env_name);
        env_name = NULL;
        free(value);
        value = NULL;
    }


out:
    if (nvs_handle) {
        nvs_close(nvs_handle);
    }
    free(env_name);
    free(value);
    nvs_flash_init_partition(DOTENV_NVS_PARTITION);
    return ret;
}
