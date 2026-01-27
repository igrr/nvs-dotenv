# nvs-dotenv Example

This example demonstrates how to use the `nvs-dotenv` component to load environment variables from a `.env` file and access them using `getenv()`.

## How it works

1. The `.env` file contains key-value pairs (e.g., `WIFI_SSID=yyyyyy`)
2. During the build, the `.env` file is converted to an NVS partition binary
3. At runtime, `nvs_dotenv_load()` loads the NVS partition
4. Variables can be accessed using the standard `getenv()` function

## Building and running

### Using the component registry

```bash
idf.py create-project-from-example "igrr/nvs-dotenv:nvs-dotenv-example"
cd nvs-dotenv-example
idf.py build
idf.py -p PORT flash monitor
```

### From this repository

```bash
cd examples/nvs-dotenv-example
idf.py build
idf.py -p PORT flash monitor
```

## Configuration

### Environment variables

Edit the `.env` file to set your own variables:

```
WIFI_SSID=your_ssid
WIFI_PASS=your_password
```

### Partition table

The example uses a custom partition table (`partitions_example.csv`) that includes a `dotenv` partition:

```csv
# Name,     Type,   SubType, Offset,  Size, Flags
nvs,        data,   nvs,           ,  24k,
factory,    app,    factory,       ,  550K,
dotenv,     data,   nvs,           ,  12k,
```

## Expected output

```
I (XXX) example: Loading environment variables
I (XXX) example: WIFI_SSID: yyyyyy
I (XXX) example: WIFI_PASS: xxxxxx
```
