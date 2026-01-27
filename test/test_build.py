#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Ivan Grokhotkov
# SPDX-License-Identifier: Apache-2.0
"""
Regression tests for nvs-dotenv build system integration.

These tests verify:
- Issue #2: dotenv.bin is created during 'idf.py build'
- Issue #4: dotenv.bin is rebuilt when .env file changes

Run with:
    pytest test_build.py -v

These are host-side build tests that don't require hardware or QEMU.
"""

import shutil
import subprocess
import time
from pathlib import Path

import pytest


PROJECT_DIR = Path(__file__).parent.parent
EXAMPLE_DIR = PROJECT_DIR / "examples" / "nvs-dotenv-example"


def run_idf_command(args: list[str], cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run an idf.py command and return the result."""
    cmd = ["idf.py"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result


@pytest.fixture
def example_project(tmp_path):
    """
    Create a temporary copy of the example project for testing.
    This ensures tests don't interfere with each other.
    """
    example_dst = tmp_path / "nvs-dotenv-example"

    # Copy example project
    shutil.copytree(EXAMPLE_DIR, example_dst)

    # Copy the component to a location where it can be found
    component_dst = tmp_path / "nvs-dotenv"
    shutil.copytree(
        PROJECT_DIR,
        component_dst,
        ignore=shutil.ignore_patterns(".git", "build", "__pycache__", "*.pyc"),
    )

    # Update the example's idf_component.yml to use the local component
    component_yml = example_dst / "main" / "idf_component.yml"
    component_yml.write_text(f"""
dependencies:
  igrr/nvs-dotenv:
    version: "*"
    override_path: "{component_dst}"
""")

    # Create sdkconfig.defaults with custom partition table
    sdkconfig_defaults = example_dst / "sdkconfig.defaults"
    sdkconfig_defaults.write_text("""
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions_example.csv"
""")

    # Create a .env file
    env_file = example_dst / ".env"
    env_file.write_text("TEST_VAR=initial_value\n")

    yield example_dst


class TestBuildDependencies:
    """Test that build dependencies work correctly."""

    def test_dotenv_bin_created_on_build(self, example_project):
        """
        Regression test for issue #2:
        https://github.com/igrr/nvs-dotenv/issues/2

        Verify that dotenv.bin is created when running 'idf.py build'.
        Previously, the nvs_dotenv_bin target was missing the ALL keyword,
        so dotenv.bin was not created during the default build.
        """
        # Set target
        result = run_idf_command(["set-target", "esp32"], example_project)
        assert result.returncode == 0, f"set-target failed:\n{result.stderr}"

        # Build the project
        result = run_idf_command(["build"], example_project)
        assert result.returncode == 0, f"build failed:\n{result.stderr}"

        # Verify dotenv.bin exists
        dotenv_bin = example_project / "build" / "dotenv.bin"
        assert dotenv_bin.exists(), (
            "dotenv.bin was not created by 'idf.py build'. "
            "This indicates the nvs_dotenv_bin target is missing the ALL keyword."
        )

    def test_dotenv_bin_rebuilt_on_env_change(self, example_project):
        """
        Regression test for issue #4:
        https://github.com/igrr/nvs-dotenv/issues/4

        Verify that dotenv.bin is rebuilt when .env file changes.
        Previously, there was a typo in the DEPENDS clause (csv_full_path
        instead of csv_path_full), causing the dependency to not be tracked.
        """
        # Initial build
        result = run_idf_command(["set-target", "esp32"], example_project)
        assert result.returncode == 0, f"set-target failed:\n{result.stderr}"

        result = run_idf_command(["build"], example_project)
        assert result.returncode == 0, f"initial build failed:\n{result.stderr}"

        dotenv_bin = example_project / "build" / "dotenv.bin"
        assert dotenv_bin.exists(), "dotenv.bin was not created"

        # Record original mtime
        original_mtime = dotenv_bin.stat().st_mtime

        # Wait to ensure mtime will be different (filesystem resolution)
        time.sleep(1.1)

        # Modify .env file
        env_file = example_project / ".env"
        env_file.write_text("TEST_VAR=modified_value\nNEW_VAR=new_value\n")

        # Rebuild
        result = run_idf_command(["build"], example_project)
        assert result.returncode == 0, f"rebuild failed:\n{result.stderr}"

        # Verify dotenv.bin was rebuilt (mtime changed)
        new_mtime = dotenv_bin.stat().st_mtime
        assert new_mtime > original_mtime, (
            f"dotenv.bin was not rebuilt after .env change. "
            f"Original mtime: {original_mtime}, new mtime: {new_mtime}. "
            f"This indicates the csv_path_full dependency is not being tracked correctly."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
