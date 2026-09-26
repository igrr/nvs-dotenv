#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ivan Grokhotkov
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for dotenv_to_csv.cmake.

The script is run with 'cmake -P', and the generated CSV file is read back the
same way nvs_partition_gen.py reads it (with csv.DictReader), so that a value
which survives these tests also survives the NVS partition generator.

Run with:
    pytest test_dotenv_to_csv.py -v
"""

import csv
import os
import subprocess
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parent.parent / 'dotenv_to_csv.cmake'


def run_script(dotenv_path: Path, csv_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['cmake', f'-DDOTENV_FILE={dotenv_path}', f'-DCSV_FILE={csv_path}', '-P', str(SCRIPT)],
        capture_output=True,
        text=True,
    )


def read_back_csv(csv_path: Path) -> dict:
    """Parse the CSV file the way nvs_partition_gen.py does."""
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        # Same reader setup as in nvs_partition_gen.py
        reader = csv.DictReader(filter(lambda row: row[0] != '#', csv_file), delimiter=',')
        rows = {row['key']: row for row in reader}

    assert rows['dotenv']['type'] == 'namespace'
    count = int(rows['count']['value'])
    return {rows[f'k{i}']['value']: rows[f'v{i}']['value'] for i in range(count)}


@pytest.fixture
def convert(tmp_path):
    """Write the given .env contents to a file, convert it and return the variables."""
    def _convert(contents: str) -> dict:
        dotenv_path = tmp_path / '.env'
        csv_path = tmp_path / 'dotenv.csv'
        dotenv_path.write_bytes(contents.encode('utf-8'))
        result = run_script(dotenv_path, csv_path)
        assert result.returncode == 0, result.stderr
        return read_back_csv(csv_path)
    return _convert


class TestDotenvParsing:
    """Test parsing of the .env file."""

    def test_simple_vars(self, convert):
        assert convert('FOO=bar\nBAZ=quux\n') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_no_trailing_newline(self, convert):
        assert convert('FOO=bar\nBAZ=quux') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_empty_file(self, convert):
        assert convert('') == {}

    def test_blank_lines_are_skipped(self, convert):
        assert convert('\nFOO=bar\n\n\nBAZ=quux\n\n') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_crlf_line_endings(self, convert):
        assert convert('FOO=bar\r\n\r\nBAZ=quux\r\n') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_cr_line_endings(self, convert):
        assert convert('FOO=bar\r# comment\rBAZ=quux\r') == {'FOO': 'bar', 'BAZ': 'quux'}

    def test_comments_are_skipped(self, convert):
        assert convert('# a comment\nFOO=bar\n  # indented comment\n') == {'FOO': 'bar'}

    def test_whitespace_around_key_and_value(self, convert):
        assert convert('  FOO = bar  \n') == {'FOO': 'bar'}

    def test_quoted_value(self, convert):
        assert convert('FOO="bar baz"\n') == {'FOO': 'bar baz'}

    def test_all_surrounding_quotes_are_removed(self, convert):
        assert convert('FOO=""bar""\n') == {'FOO': 'bar'}

    def test_quotes_keep_surrounding_whitespace(self, convert):
        assert convert('FOO="  bar  "\n') == {'FOO': '  bar  '}

    def test_hash_inside_value_is_not_a_comment(self, convert):
        assert convert('FOO=bar # not a comment\n') == {'FOO': 'bar # not a comment'}

    def test_no_variable_interpolation(self, convert):
        assert convert('FOO=$BAR\nBAZ=${FOO}\n') == {'FOO': '$BAR', 'BAZ': '${FOO}'}

    def test_empty_value(self, convert):
        assert convert('FOO=\n') == {'FOO': ''}

    def test_value_may_contain_equals_sign(self, convert):
        assert convert('FOO=a=b\n') == {'FOO': 'a=b'}

    def test_value_may_contain_commas(self, convert):
        assert convert('FOO=a,b,c\n') == {'FOO': 'a,b,c'}

    def test_last_definition_wins(self, convert):
        """A redefined variable keeps its original position, like a Python dict."""
        result = convert('FOO=1\nBAR=2\nFOO=3\n')
        assert result == {'FOO': '3', 'BAR': '2'}
        assert list(result) == ['FOO', 'BAR']

    @pytest.mark.parametrize(
        'contents, bad_line',
        [
            ('FOO=bar\nnot a variable\n', 'not a variable'),
            # Last line, without a line break
            ('FOO=bar\nPARENT_SCOPE', 'PARENT_SCOPE'),
        ],
    )
    def test_line_without_equals_sign_is_an_error(self, tmp_path, contents, bad_line):
        dotenv_path = tmp_path / '.env'
        dotenv_path.write_text(contents)
        result = run_script(dotenv_path, tmp_path / 'dotenv.csv')
        assert result.returncode != 0
        # CMake wraps error messages, so the line break may fall anywhere
        stderr = ' '.join(result.stderr.split())
        assert 'line 2:' in stderr
        assert f"got '{bad_line}'" in stderr


class TestSpecialCharacters:
    """Test that values survive the trip through the CSV file."""

    @pytest.mark.parametrize(
        'value',
        [
            'home/temperature,home/humidity',
            'a,b,c,d',
            ',leading comma',
            'trailing comma,',
            'say "hi" there',
            'both "quotes, and commas" here',
            'with spaces',
            '# not a comment',
            'привет',
            # Characters which are special in CMake
            'a;b;c',
            'a;;b;',
            ';',
            '[[bracket]]',
            'back\\slash\\',
            '\\;',
            '@FOO@',
            '"',
            # Keywords of CMake's set() command
            'PARENT_SCOPE',
            'CACHE',
            'CACHE STRING',
        ],
        ids=lambda v: repr(v),
    )
    def test_special_characters_in_value(self, convert, value):
        """
        Values are written to the CSV file which nvs_partition_gen.py reads with
        csv.DictReader, so commas and quotes have to be escaped; and they are
        handled by a CMake script, which must not split them on semicolons.
        """
        expected = value.strip('"')
        assert convert(f'FOO={value}\n') == {'FOO': expected}

    @pytest.mark.parametrize('name', ['A,B', 'A;B', 'A"B', 'PARENT_SCOPE', 'CACHE'], ids=lambda v: repr(v))
    def test_special_characters_in_name(self, convert, name):
        assert convert(f'{name}=value\n') == {name: 'value'}


class TestOutputFile:
    """Test how the CSV file is written."""

    def test_exact_output(self, tmp_path):
        dotenv_path = tmp_path / '.env'
        csv_path = tmp_path / 'dotenv.csv'
        dotenv_path.write_text('FOO=bar\nLIST=a,"b"\n')
        assert run_script(dotenv_path, csv_path).returncode == 0
        assert csv_path.read_text() == (
            'key,type,encoding,value\n'
            'dotenv,namespace,,\n'
            'k0,data,string,FOO\n'
            'v0,data,binary,bar\n'
            'k1,data,string,LIST\n'
            'v1,data,binary,"a,""b"\n'
            'count,data,u32,2\n'
        )

    def test_missing_dotenv_file(self, tmp_path):
        csv_path = tmp_path / 'dotenv.csv'
        result = run_script(tmp_path / 'does-not-exist', csv_path)
        assert result.returncode == 0, result.stderr
        assert 'not found' in result.stderr
        assert read_back_csv(csv_path) == {}

    def test_unchanged_csv_is_not_rewritten(self, tmp_path):
        """The NVS image is regenerated when the CSV file's mtime changes."""
        dotenv_path = tmp_path / '.env'
        csv_path = tmp_path / 'dotenv.csv'
        dotenv_path.write_text('FOO=bar\n')
        assert run_script(dotenv_path, csv_path).returncode == 0
        old_mtime = time.time() - 100
        os.utime(csv_path, (old_mtime, old_mtime))

        assert run_script(dotenv_path, csv_path).returncode == 0
        assert csv_path.stat().st_mtime == old_mtime

        dotenv_path.write_text('FOO=baz\n')
        assert run_script(dotenv_path, csv_path).returncode == 0
        assert csv_path.stat().st_mtime != old_mtime
        assert read_back_csv(csv_path) == {'FOO': 'baz'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
