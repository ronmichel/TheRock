import logging
import os
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent
if os.name == 'nt':
    cmd = [
        f"ctest",
        f"--test-dir",
        f"{THEROCK_BIN_DIR}/catch_tests"
    ]
else:
    cmd = [
        f"ls ${THEROCK_BIN_DIR} && ls ${THEROCK_BIN_DIR}/.. && ctest", # For debug, need to remove it
        f"--test-dir",
        f"{THEROCK_BIN_DIR}/catch_tests"
    ]

logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmd)}")
subprocess.run(cmd, cwd=THEROCK_DIR, check=True)
