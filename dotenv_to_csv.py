#!/usr/bin/env python3

import argparse
import csv
import io
import typing as t
import sys


class DotenvSyntaxError(Exception):
    pass


def get_env_vars_from_dotenv(dotenv_file: t.TextIO) -> t.Dict[str, str]:
    env_vars = {}
    for lineno, line in enumerate(dotenv_file, start=1):
        # Iterating over a file yields the line terminator as well, so strip it
        # first: otherwise an empty line is '\n' rather than '' and isn't skipped.
        line = line.strip()
        # ignore empty lines and comments
        if not line or line.startswith('#'):
            continue
        # The line should be in format VAR_NAME=value, value may be quoted
        if '=' not in line:
            raise DotenvSyntaxError(f'line {lineno}: expected VAR_NAME=value, got {line!r}')
        key, value = line.split('=', 1)
        value = value.strip().strip('"')
        # We could try to add variable interpolation here
        env_vars[key.strip()] = value
    return env_vars

def write_env_vars_to_csv(env_vars: t.Dict[str, str], csv_file: t.TextIO) -> None:
    # prepare the CSV file for NVS partition generator.
    # Use csv.writer rather than plain string formatting, so that values
    # containing commas or quotes are escaped: nvs_partition_gen.py reads the
    # file with csv.DictReader and would otherwise truncate such values.
    writer = csv.writer(csv_file, lineterminator='\n')
    writer.writerow(['key', 'type', 'encoding', 'value'])
    # write namespace entry
    writer.writerow(['dotenv', 'namespace', '', ''])
    for index, (var, value) in enumerate(env_vars.items()):
        writer.writerow([f'k{index}', 'data', 'string', var])
        writer.writerow([f'v{index}', 'data', 'binary', value])
    writer.writerow(['count', 'data', 'u32', len(env_vars)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('dotenv_file', help='Path of input .env file',
                        type=str)
    parser.add_argument('csv_file', help='Path of the output .csv file',
                        type=str)
    args = parser.parse_args()

    print(f'Processing dotenv file ({args.dotenv_file})', file=sys.stderr)

    # nvs_partition_gen.py reads the CSV file as UTF-8, so don't leave the
    # encoding up to the locale.
    try:
        with open(args.dotenv_file, 'r', encoding='utf-8') as dotenv_file:
            env_vars = get_env_vars_from_dotenv(dotenv_file)
    except FileNotFoundError:
        print(f'Dotenv file ({args.dotenv_file}) not found, no environment variables will be saved in NVS', file=sys.stderr)
        env_vars = {}
    except DotenvSyntaxError as e:
        raise SystemExit(f'{args.dotenv_file}: {e}')
    
    try:
        with open(args.csv_file, 'r', encoding='utf-8') as csv_file:
            old_csv_content = csv_file.read()
    except FileNotFoundError:
        old_csv_content = ''
    

    new_csv_file = io.StringIO()
    write_env_vars_to_csv(env_vars, new_csv_file)
    new_csv_content = new_csv_file.getvalue()

    if new_csv_content == old_csv_content:
        # Don't update the resulting file if no changes are required
        return
    
    with open(args.csv_file, 'w', encoding='utf-8') as csv_file:
        csv_file.write(new_csv_content)


if __name__ == '__main__':
    main()
