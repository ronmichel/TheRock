"""
This file provides universal ctest run functionality.

Due to ctest's parallelization, there are flaky tests that are unable to run or retry due to failure.
These flaky results are not particular to any test suite or any executable.
To avoid this issue, the `run_ctest_exectuables` allow re-run capability for "Not Run" tests
"""

import logging
import os
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent

logging.basicConfig(level=logging.INFO)


def run_ctest_executables(
    timeout=300, repeat=False, smoke_tests=[], test_name="", tests_to_ignore=[]
):
    cmd = [
        "ctest",
        "--test-dir",
        f"{THEROCK_BIN_DIR}/{test_name}",
        "--output-on-failure",
        "--parallel",
        "8",
        "--timeout",
        timeout,
    ]

    if repeat:
        cmd += ["--repeat", "until-pass:3"]

    if tests_to_ignore:
        cmd += ["--exclude-regex", "|".join(tests_to_ignore)]

    # If smoke tests are enabled, we run smoke tests only.
    # Otherwise, we run the normal test suite
    environ_vars = os.environ.copy()
    test_type = os.getenv("TEST_TYPE", "full")
    if test_type == "smoke" and smoke_tests:
        environ_vars["GTEST_FILTER"] = ":".join(smoke_tests)

    logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmd)}")
    subprocess.run(cmd, cwd=THEROCK_DIR, check=True, env=environ_vars)

    # Add re-try capability here for single tests and collect exit_codes
