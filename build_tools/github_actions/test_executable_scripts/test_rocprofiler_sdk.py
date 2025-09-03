import logging
import os
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent

OUTPUT_ARTIFACTS_DIR = os.getenv("OUTPUT_ARTIFACTS_DIR")

logging.basicConfig(level=logging.INFO)

# Env setup
env_init_cmd = [
    "export",
    "HIP_PLATFORM=amd"
]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(env_init_cmd)}")
subprocess.run(
    env_init_cmd,
    cwd=THEROCK_DIR,
    check=True
)

# Dependencies setup (remove once Dockerfile is updated)
dep_init_cmd = [
    "sudo",
    "apt-get",
    "install",
    "-y",
    "build-essential",
    "libdw-dev",
    "pkg-config",
    "libopenmpi-dev"
]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(dep_init_cmd)}")
subprocess.run(
    dep_init_cmd,
    cwd=THEROCK_DIR,
    check=True
)

# CMake Init
cmake_init_cmd = [
    "cmake",
    "-B",
    "/tmp/rocprofiler-sdk-build-tests",
    f"-DCMAKE_PREFIX_PATH={OUTPUT_ARTIFACTS_DIR}",
    f"{OUTPUT_ARTIFACTS_DIR}/share/rocprofiler-sdk/tests"
]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmake_init_cmd)}")
subprocess.run(
    cmake_init_cmd,
    cwd=THEROCK_DIR,
    check=True
)

# Cmake Build
cmake_cmd = [
    "cmake",
    "--build",
    "/tmp/rocprofiler-sdk-build-tests",
    "--target",
    "all",
    "--parallel",
    "8"
]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmake_cmd)}")
subprocess.run(
    cmake_cmd,
    cwd=THEROCK_DIR,
    check=True
)

# CTest Run Tests
ctest_cmd = [
    "ctest",
    "--test-dir",
    "/tmp/rocprofiler-sdk-build-tests",
    "--output-on-failure"
]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(ctest_cmd)}")
subprocess.run(
    ctest_cmd,
    cwd=THEROCK_DIR,
    check=True
)