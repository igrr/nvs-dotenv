#!/usr/bin/env python3

import argparse
import io
import typing as t
import sys


def get_env_vars_from_dotenv(dotenv_file: t.TextIO) -> t.Dict[str, str]:
    env_vars = {}
    for line in dotenv_file:
        # ignore empty lines and comments
        if not line or line.startswith('#'):
            continue
        # The line should be in format VAR_NAME=value, value may be quoted
        key, value = line.split('=', 1)
        value = value.strip().strip('"')
        # We could try to add variable interpolation here
        env_vars[key] = value
    return env_vars

def write_env_vars_to_csv(env_vars: t.Dict[str, str], csv_file: t.TextIO) -> None:
    # prepare the CSV file for NVS partition generator
    csv_file.write('key,type,encoding,value\n')
    # write namespace entry
    csv_file.write('dotenv,namespace,,\n')
    for index, (var, value) in enumerate(env_vars.items()):
        key_name = f'k{index}'
        value_name = f'v{index}'
        csv_file.write(f'{key_name},data,string,{var}\n')
        csv_file.write(f'{value_name},data,binary,{value}\n')
    csv_file.write(f'count,data,u32,{len(env_vars)}\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('dotenv_file', help='Path of input .env file',
                        type=str)
    parser.add_argument('csv_file', help='Path of the output .csv file',
                        type=str)
    args = parser.parse_args()

    print(f'Processing dotenv file ({args.dotenv_file})', file=sys.stderr)

    try:
        with open(args.dotenv_file, 'r') as dotenv_file:
            env_vars = get_env_vars_from_dotenv(dotenv_file)
    except FileNotFoundError:
        print(f'Dotenv file ({args.dotenv_file}) not found, no environment variables will be saved in NVS', file=sys.stderr)
        env_vars = {}
    
    try:
        with open(args.csv_file, 'r') as csv_file:
            old_csv_content = csv_file.read()
    except FileNotFoundError:
        old_csv_content = ''
    

    new_csv_file = io.StringIO()
    write_env_vars_to_csv(env_vars, new_csv_file)
    new_csv_content = new_csv_file.getvalue()

    if new_csv_content == old_csv_content:
        # Don't update the resulting file if no changes are required
        return
    
    with open(args.csv_file, 'w') as csv_file:
        csv_file.write(new_csv_content)


if __name__ == '__main__':
    main()
