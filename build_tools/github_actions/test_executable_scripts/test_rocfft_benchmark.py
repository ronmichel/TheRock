import logging
import os
import re
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent

logging.basicConfig(level=logging.INFO)

# Lengths
length_list = [
    "16777216",
    "14348907",
    "9765625",
    "4096 4096",
    "6561 6561",
    "3125 3125",
    "256 256 256",
    "243 243 243",
    "125 125 125",
    "100 100 100 -t 2 -o",
    "100 100 100 -t 3 -o",
    "200 200 200 -t 2 -o",
    "200 200 200 -t 3 -o",
    "192 192 192 -t 2 -o",
    "192 192 192 -t 3 -o",
    "64 64 64 -t 2 -o",
    "60 -b 1024",
    "336 336 56 --double -o"
]

for length in length_list:
    # Default batch size is 10. For specific batch size, please add batch size
    # Along with length in length_list below logic will retrieve and replace the default batch size
    batch_size = 10
    explict_batch_size = re.search(r'-b\s+(\d+)', length)
    if explict_batch_size:
        batch_size = explict_batch_size.group(1)
        length = re.sub(r'-b\s+\d+', "", length)
    cmd = [
        f"{THEROCK_BIN_DIR}/rocfft-bench",
        "--length",
        *[f"{item}" for item in length.split()],
        "-b",
        f"{batch_size}",
        "-N",
        "20"
    ]
    logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmd)}")
    subprocess.run(
        cmd,
        cwd=THEROCK_DIR,
        check=True,
    )
