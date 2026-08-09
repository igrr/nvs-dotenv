def test_nvs_dotenv_example(dut):
    """Test that environment variables are loaded correctly."""
    dut.expect('Loading environment variables', timeout=30)
    dut.expect('WIFI_SSID: yyyyyy', timeout=10)
    dut.expect('WIFI_PASS: xxxxxx', timeout=10)
    # Values containing commas must not be truncated at the comma
    dut.expect('MQTT_TOPICS: home/temperature,home/humidity', timeout=10)
