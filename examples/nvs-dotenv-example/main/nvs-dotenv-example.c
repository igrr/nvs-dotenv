#include "esp_log.h"
#include "esp_err.h"
#include "nvs_dotenv.h"

static const char *TAG = "example";

static void log_env_var(const char *name)
{
    const char *value = getenv(name);
    if (value == NULL) {
        value = "(not set)";
    }
    ESP_LOGI(TAG, "%s: %s", name, value);
}

void app_main(void)
{
    ESP_LOGI(TAG, "Loading environment variables");
    ESP_ERROR_CHECK(nvs_dotenv_load());

    log_env_var("WIFI_SSID");
    log_env_var("WIFI_PASS");
    /* Values may contain commas */
    log_env_var("MQTT_TOPICS");
}
