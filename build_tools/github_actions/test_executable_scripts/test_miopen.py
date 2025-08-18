import logging
import os
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent

logging.basicConfig(level=logging.INFO)

###########################################

positive_filter = []
negative_filter = []

# Fusion #
positive_filter.append("*GPU_KernelTuningNetTestConv*")

gtest_final_filter_cmd = (
    "--gtest_filter=" + ":".join(positive_filter) + "-" + ":".join(negative_filter)
)

#############################################

cmd = [f"MIOPEN_LOG_LEVEL=7 {THEROCK_BIN_DIR}/miopen_gtest", gtest_final_filter_cmd]
logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmd)}")
subprocess.run(
    cmd,
    cwd=THEROCK_DIR,
    check=True,
)
