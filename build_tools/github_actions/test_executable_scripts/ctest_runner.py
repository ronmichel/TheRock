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


def read_ctest_test_log(file_path):
    if file_path.exists() and file_path.stat().st_size > 0:
        return [
            line.strip() for line in file_path.read_text().splitlines() if line.strip()
        ]
    return []


def ctest_retry_failed_test(test_name, timeout_seconds, environ_vars):
    failed_file_logs = (
        THEROCK_BIN_DIR / test_name / "Testing" / "Temporary" / "LastTestsFailed.log"
    )

    failed_tests = read_ctest_test_log(failed_file_logs)
    if failed_tests:
        logging.info(
            f"Failed tests ({len(failed_tests)}): {failed_tests}\nRe-running tests..."
        )
        # Sometimes, parallel runs of ctest executables cause resource locks or race conditions.
        # This results in ctest executables with status "Process not started" and marked as "Not Run", resulting in failures
        # This is the reason for not parallelism in this subprocess run.
        cmd = [
            "ctest",
            "--test-dir",
            f"{THEROCK_BIN_DIR}/{test_name}",
            "--parallel",
            "1",
            "--timeout",
            timeout_seconds,
            "--repeat",
            "until-pass:3",
        ]
        subprocess.run(cmd, cwd=THEROCK_DIR, check=True, env=environ_vars)


def run_ctest_executables(
    timeout_seconds="300",
    repeat=False,
    smoke_tests=[],
    test_name="",
    tests_to_ignore=[],
):
    cmd = [
        "ctest",
        "--test-dir",
        f"{THEROCK_BIN_DIR}/{test_name}",
        "--parallel",
        "8",
        "--timeout",
        timeout_seconds,
    ]

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

    # After test "failures" or "not run" status, those tests are written to "LastTestsFailed.log"
    # In the case that the flag "repeat" is requested, we re-run those failed tests
    if repeat:
        ctest_retry_failed_test(
            test_name=test_name,
            timeout_seconds=timeout_seconds,
            environ_vars=environ_vars,
        )
