def test_nvs_dotenv_example(dut):
    """Test that environment variables are loaded correctly."""
    dut.expect_exact('Loading environment variables', timeout=30)
    dut.expect_exact('WIFI_SSID: yyyyyy', timeout=10)
    dut.expect_exact('WIFI_PASS: xxxxxx', timeout=10)
    dut.expect_exact('MQTT_TOPICS: home/temperature,home/humidity', timeout=10)
