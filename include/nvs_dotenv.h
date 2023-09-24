#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Load environment variables from NVS
 *
 * @return ESP_OK on success
 */
esp_err_t nvs_dotenv_load(void);


#ifdef __cplusplus
}
#endif
