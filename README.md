# nvs-dotenv

[![Component Registry](https://components.espressif.com/components/igrr/nvs-dotenv/badge.svg)](https://components.espressif.com/components/igrr/nvs-dotenv)

`nvs-dotenv` is an ESP-IDF component which makes variables defined in a `.env` file accessible using `getenv` function:

- Create a `.env` file inside you project directory
- Keep various local configs and secrets in `.env` — Wi-Fi credentials, API tokens, and so on.
- In your ESP-IDF application, call `getenv` function to access these variables

With `nvs-dotenv`, you won't have to:
- hardcode credentials in your application source code
- store the credentials in sdkconfig, and wait for the entire app to rebuild when you change them.

`nvs-dotenv` is intended to be used mainly during the development phase. In a production device you will likely need a provisioning workflow of some sort.

## Using the component

1. In an existing ESP-IDF project, run the following command to install the component:
   ```bash
   idf.py add-dependency "igrr/nvs-dotenv"
   ```
2. Edit your partition table, adding a new partition:
   ```csv
   # Name,     Type,   SubType, Offset,  Size, Flags
   dotenv,     data,   nvs,           ,  12k,
   ```
3. Create a `.env` file in your project directory:
   ```
   WIFI_SSID=yyyyyy
   WIFI_PASS=xxxxxx
   ```
4. In the application, initialize `nvs-dotenv`:
   ```c++
   ESP_ERROR_CHECK(nvs_dotenv_load());
   ```
5. Now you can access variables from `.env` using `getenv`:
   ```c++
   const char *ssid = getenv("WIFI_SSID");
   ```


## Example

This component includes an example illustrating the above steps. You can try the example as follows:

```bash
idf.py create-project-from-example "igrr/nvs-dotenv:nvs-dotenv-example"
```

Then build as usual:
```bash
cd nvs-dotenv-example
idf.py build
```

And flash it to the board:
```bash
idf.py -p PORT flash monitor
```

The output should be:
```
I (3263) example: Loading environment variables
I (6033) example: WIFI_SSID: yyyyyy
I (6053) example: WIFI_PASS: xxxxxx
```

## License

This component is provided under Apache 2.0 license, see [LICENSE](LICENSE.md) file for details.
