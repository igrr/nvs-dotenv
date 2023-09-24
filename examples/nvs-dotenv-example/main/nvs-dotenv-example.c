#include "esp_log.h"
#include "esp_err.h"
#include "nvs_dotenv.h"

static const char *TAG = "example";

void app_main(void)
{
    ESP_LOGI(TAG, "Loading environment variables");
    ESP_ERROR_CHECK(nvs_dotenv_load());

    const char *wifi_ssid = getenv("WIFI_SSID");
    if (wifi_ssid == NULL) {
        wifi_ssid = "(not set)";
    }
    ESP_LOGI(TAG, "WIFI_SSID: %s", wifi_ssid);

    const char *wifi_pass = getenv("WIFI_PASS");
    if (wifi_pass == NULL) {
        wifi_pass = "(not set)";
    }
    ESP_LOGI(TAG, "WIFI_PASS: %s", wifi_pass);
}
