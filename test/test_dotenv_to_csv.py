#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ivan Grokhotkov
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for dotenv_to_csv.py.

The generated CSV file is read back the same way nvs_partition_gen.py reads it
(with csv.DictReader), so that a value which survives these tests also survives
the NVS partition generator.

Run with:
    pytest test_dotenv_to_csv.py -v
"""

import csv
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv_to_csv import (  # noqa: E402
    DotenvSyntaxError,
    get_env_vars_from_dotenv,
    write_env_vars_to_csv,
)


def parse_dotenv(contents: str) -> dict:
    return get_env_vars_from_dotenv(io.StringIO(contents))


def read_back_csv(env_vars: dict) -> dict:
    """
    Write the variables to a CSV file and read them back out of it, parsing the
    CSV the way nvs_partition_gen.py does.
    """
    csv_file = io.StringIO()
    write_env_vars_to_csv(env_vars, csv_file)
    csv_file.seek(0)

    # Same reader setup as in nvs_partition_gen.py
    reader = csv.DictReader(filter(lambda row: row[0] != '#', csv_file), delimiter=',')
    rows = {row['key']: row for row in reader}

    count = int(rows['count']['value'])
    return {rows[f'k{i}']['value']: rows[f'v{i}']['value'] for i in range(count)}


class TestDotenvParsing:
    """Test parsing of the .env file."""

    def test_simple_vars(self):
        assert parse_dotenv('FOO=bar\nBAZ=quux\n') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_blank_lines_are_skipped(self):
        """
        A line read from a file keeps its trailing newline, so an empty line is
        '\\n' rather than ''. It has to be stripped before the emptiness check,
        otherwise parsing a .env file with blank lines fails.
        """
        assert parse_dotenv('\nFOO=bar\n\n\nBAZ=quux\n\n') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_comments_are_skipped(self):
        assert parse_dotenv('# a comment\nFOO=bar\n  # indented comment\n') == {'FOO': 'bar'}

    def test_whitespace_around_key_and_value(self):
        assert parse_dotenv('  FOO = bar  \n') == {'FOO': 'bar'}

    def test_quoted_value(self):
        assert parse_dotenv('FOO="bar baz"\n') == {'FOO': 'bar baz'}

    def test_empty_value(self):
        assert parse_dotenv('FOO=\n') == {'FOO': ''}

    def test_value_may_contain_equals_sign(self):
        assert parse_dotenv('FOO=a=b\n') == {'FOO': 'a=b'}

    def test_value_may_contain_commas(self):
        assert parse_dotenv('FOO=a,b,c\n') == {'FOO': 'a,b,c'}

    def test_line_without_equals_sign_is_an_error(self):
        with pytest.raises(DotenvSyntaxError, match='line 2'):
            parse_dotenv('FOO=bar\nnot a variable\n')


class TestCsvRoundtrip:
    """Test that values survive the trip through the CSV file."""

    def test_simple_vars(self):
        assert read_back_csv({'FOO': 'bar', 'BAZ': 'quux'}) == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_no_vars(self):
        assert read_back_csv({}) == {}

    @pytest.mark.parametrize(
        'value',
        [
            'home/temperature,home/humidity',
            'a,b,c,d',
            ',leading comma',
            'trailing comma,',
            'say "hi"',
            'both "quotes, and commas"',
            'with spaces',
        ],
        ids=lambda v: repr(v),
    )
    def test_special_characters_in_value(self, value):
        """
        Regression test for values containing commas: the CSV file is read back
        with csv.DictReader, so an unquoted comma in a value used to shift the
        rest of the value into columns the reader ignores, silently truncating
        the value at the first comma.
        """
        assert read_back_csv({'FOO': value}) == {'FOO': value}

    def test_special_characters_in_name(self):
        assert read_back_csv({'A,B': 'value'}) == {'A,B': 'value'}


class TestEndToEnd:
    """Test the whole .env -> CSV conversion."""

    def test_dotenv_with_comma_separated_value(self):
        dotenv = (
            '# Wi-Fi credentials\n'
            'WIFI_SSID=yyyyyy\n'
            '\n'
            'MQTT_TOPICS=home/temperature,home/humidity\n'
        )
        assert read_back_csv(parse_dotenv(dotenv)) == {
            'WIFI_SSID': 'yyyyyy',
            'MQTT_TOPICS': 'home/temperature,home/humidity',
        }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
