#!/usr/bin/env python3
"""PyTorch ROCm Pytest Runner with additional test exclusion capabilities.

This script runs PyTorch unit tests using pytest with additional test exclusion
capabilities tailored for AMD ROCm GPUs.

Test Exclusion Criteria
------------------------
Tests may be skipped based on:
- AMDGPU family compatibility (e.g., gfx942, gfx1151)
- PyTorch version-specific issues
- Known failures not yet upstreamed to PyTorch

Environment Variables
---------------------
THEROCK_ROOT_DIR : str, optional
                   Root directory of TheRock project.
                   If not set, auto-detected from script location.
AMDGPU_FAMILY :     str, optional
                    Target AMDGPU family for testing (e.g., "gfx942", "gfx94X").
                    Names should match those in "TheRock/cmake/therock_amdgpu_targets.cmake".
                    Supports wildcards (e.g., "gfx94X" matches any gfx94* architecture).
                    If not set, auto-detects from available hardware using PyTorch.
PYTORCH_VERSION :   str, optional
                    PyTorch version for version-specific test filtering (e.g., "2.10").
                    Format: "major.minor" as string.
                    If not set, auto-detects from installed PyTorch package.

Usage Examples
--------------
Basic usage (auto-detect everything):
    $ python run_linux_pytorch_tests.py

Debug mode (run only skipped tests):
    $ python run_linux_pytorch_tests.py --debug

Custom test selection with pytest -k:
    $ python run_linux_pytorch_tests.py -k "test_nn and not test_dropout"

Disable pytest cache (useful in containers):
    $ python run_linux_pytorch_tests.py --no-cache

Exit Codes
----------
0 : All tests passed
1 : Test failures or collection errors
Other : Pytest-specific error codes

Side-effects
-----
- This script modifies PYTHONPATH and sys.path to include PyTorch test directory
- Creates a temporary MIOpen cache directory for each run
- Sets HIP_VISIBLE_DEVICES environment variable to select specific GPU(s) for testing
- Runs tests sequentially (--numprocesses=0) by default
"""

import argparse
import os
import subprocess
import sys
import tempfile

from skip_tests.create_skip_tests import *
from importlib.metadata import version
from pathlib import Path

import pytest
import torch


def setup_env(pytorch_dir: str) -> None:
    """Set up environment variables required for PyTorch testing with ROCm.

    Args:
        pytorch_dir: Path to the PyTorch directory containing test files.

    Side effects:
        - Sets multiple environment variables for PyTorch testing
        - Creates a temporary directory for MIOpen cache
        - Modifies sys.path to include the test directory
    """
    os.environ["PYTORCH_PRINT_REPRO_ON_FAILURE"] = "0"
    os.environ["PYTORCH_TEST_WITH_ROCM"] = "1"
    os.environ["MIOPEN_CUSTOM_CACHE_DIR"] = tempfile.mkdtemp()
    os.environ["PYTORCH_TESTING_DEVICE_ONLY_FOR"] = "cuda"

    old_pythonpath = os.getenv("PYTHONPATH", "")
    test_dir = f"{pytorch_dir}/test"

    if old_pythonpath:
        os.environ["PYTHONPATH"] = f"{test_dir}:{old_pythonpath}"
    else:
        os.environ["PYTHONPATH"] = test_dir

    # Force update the PYTHONPATH to be part of the sys path
    # Otherwise our current python process that will run pytest will NOT
    # find it and pytest will crash!
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)


def cmd_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""
Runs PyTorch pytest for AMD GPUs. Skips additional tests compared to upstream.
Additional tests to be skipped can be tuned by PyTorch version and amdgpu family.
"""
    )

    amdgpu_family = os.getenv("AMDGPU_FAMILY")
    parser.add_argument(
        "--amdgpu-family",
        type=str,
        default=amdgpu_family if amdgpu_family is not None else "",
        required=False,
        help="""Amdgpu family (e.g. "gfx942").
Select (potentially) additional tests to be skipped based on the amdgpu family""",
    )

    pytorch_version = os.getenv("PYTORCH_VERSION")
    parser.add_argument(
        "--pytorch-version",
        type=str,
        default=pytorch_version if pytorch_version is not None else "",
        required=False,
        help="""Pytorch version (e.g. "2.7" or "all").
Select (potentially) additional tests to be skipped based on the Pytorch version.
'All' is also possible. Then all skip tests for all pytorch versions are included.
If no PyTorch version is given, it is auto-determined by the PyTorch used to run pytest.""",
    )

    env_root_dir = os.getenv("THEROCK_ROOT_DIR")
    parser.add_argument(
        "--the-rock-root-dir",
        default=env_root_dir if env_root_dir is not None else "",
        required=False,
        help="""Overwrites the root directory of TheRock.
By default TheRock root dir is determined based on this script's location.""",
    )

    parser.add_argument(
        "--debug",
        default=False,
        required=False,
        action=argparse.BooleanOptionalAction,
        help="""Inverts the selection. Only runs skipped tests.""",
    )

    parser.add_argument(
        "-k",
        default="",
        required=False,
        help="""Overwrites the pytest -k option that decides which tests should be run or skipped""",
    )

    parser.add_argument(
        "--no-cache",
        default=False,
        required=False,
        action=argparse.BooleanOptionalAction,
        help="""Disable pytest caching. Useful when only having read-only access to pytorch directory""",
    )

    args = parser.parse_args(argv)
    return args

def get_visible_gpu_list():
    """Get a list of GPUs that are visible for the torch.

       Note that the current torch build does not neccessarily have
       a support for all of the GPU's that are visible.

       The list of GPU's that are supported by the current torch build
       can be queried with method torch.cuda.get_arch_list()

        Returns:
            List of AMDGPU family strings visible.
    """
    ret = []
    if torch.cuda.is_available():
        cnt_gpu = torch.cuda.device_count()
        print(f"GPU count visible for pytorch: {cnt_gpu}")
        for ii in range(cnt_gpu):
            cuda_id = "cuda:" + str(ii)
            device = torch.cuda.device(cuda_id)
            if device:
                device_prop = torch.cuda.get_device_properties(device)
                if device_prop and hasattr(device_prop, 'gcnArchName'):
                    # amd gpu's have gcnArchName
                    ret.append(device_prop.gcnArchName)
    return ret


def detect_amdgpu_family(amdgpu_family: str = "") -> list[str]:
    """Detect and configure AMDGPU family using PyTorch.

    This function always queries PyTorch to get available GPUs and sets
    HIP_VISIBLE_DEVICES to select the appropriate GPU(s) for testing.

    Args:
        amdgpu_family: AMDGPU family string. Can be:
            - Empty string (default): Auto-detect and use first GPU (index 0)
            - Specific arch (e.g., "gfx1151"): Find and use matching GPU
            - Wildcard family (e.g., "gfx94X"): Find all matching GPUs

    Returns:
        List of detected AMDGPU family strings. Exits on failure.

    Side effects:
        Sets HIP_VISIBLE_DEVICES environment variable to comma-separated GPU indices.
    """
    try:
        # Query available GPUs
        if not torch.cuda.is_available():
            print("[ERROR] ROCm is not available or not detected by PyTorch")
            sys.exit(1)

        gpu_list_visible = get_visible_gpu_list()
        gpu_list_supported = torch.cuda.get_arch_list()

        if len(gpu_list_supported) == 0:
            print("[ERROR] No AMD GPUs detected by PyTorch")
            sys.exit(1)

        print(f"AMD GPUs supported by Pytorch build: {gpu_list_supported}")
        print(f"AMD GPUs visible: {gpu_list_visible}")

        # Determine which GPU to use based on input
        selected_gpu_indices = []
        selected_gpu_archs = []

        if not amdgpu_family:
            # Mode 1: Auto-detect
            # use first available GPU that is both visible and supported
            for idx, gpu_arch in enumerate(gpu_list_visible):
                if gpu_arch in gpu_list_supported:
                    selected_gpu_indices = [idx]
                    selected_gpu_archs = [gpu_arch]
            if len(selected_gpu_archs) == 0:
                print(f"[ERROR] No GPU found that is supported by pytorch build.")
                print(f"    AMD GPUs supported by pytorch build: {gpu_list_supported}")
                print(f"    AMD GPUs visible: {gpu_list_visible}")
                sys.exit(1)
            print(f"AMDGPU Arch auto-detected")
            print(f"    GPU arch_list: {selected_gpu_archs}")
            print(f"    GPU index list: {selected_gpu_indices}")
        elif amdgpu_family.split("-")[0].upper().endswith("X"):
            # Mode 2: Wildcard match (e.g., "gfx94X" matches "gfx942", "gfx940", etc.)
            family_part = amdgpu_family.split("-")[0]
            partial_match = family_part[:-1]  # Remove the 'X'
            print(f"family_part: {family_part}")
            print(f"partial_match: {partial_match}")
            # validate that the matched gpu is also available both in the
            # - gpu list visible for the pytorch
            # - gpu list supported by the current pytorch build
            for idx, gpu_arch in enumerate(gpu_list_visible):
                if gpu_arch in gpu_list_supported and partial_match in gpu_arch:
                    selected_gpu_indices += [idx]
                    selected_gpu_archs += [gpu_arch]
            if len(selected_gpu_archs) == 0:
                print(f"[ERROR] No GPU found matching wildcard pattern '{amdgpu_family}'.")
                print(f"    AMD GPUs supported by pytorch build: {gpu_list_supported}")
                print(f"    AMD GPUs visible: {gpu_list_visible}")
                sys.exit(1)
            print(f"AMDGPU Arch detected via wildcard match: {partial_match}")
            print(f"    GPU arch_list: {selected_gpu_archs}")
            print(f"    GPU index list: {selected_gpu_indices}")
        else:
            # Mode 3: Specific GPU arch
            # validate that the matched gpu is also available both in the
            # - gpu list visible for the pytorch
            # - gpu list supported by the current pytorch build
            for idx, gpu_arch in enumerate(gpu_list_visible):
                if gpu_arch in gpu_list_supported:
                    if gpu_arch == amdgpu_family or amdgpu_family in gpu_arch:
                        selected_gpu_indices += [idx]
                        selected_gpu_archs += [gpu_arch]
                        print(
                            f"AMDGPU Arch validated: {selected_gpu_archs} "
                            f"(GPU indices {selected_gpu_indices})"
                        )
                        break
            if len(selected_gpu_archs) == 0:
                print(f"[ERROR] Requested GPU '{amdgpu_family}' not found in available GPUs.")
                print(f"    AMD GPUs supported by pytorch build: {gpu_list_supported}")
                print(f"    AMD GPUs visible: {gpu_list_visible}")
                sys.exit(1)

        # Set HIP_VISIBLE_DEVICES to select the specific GPU
        str_indices = ",".join(str(idx) for idx in selected_gpu_indices)
        os.environ["HIP_VISIBLE_DEVICES"] = str_indices
        print("Adjusting the list of GPUs visible for ROCM/Pytorch:")
        print(f"    HIP_VISIBLE_DEVICES={str_indices}")

        return selected_gpu_archs

    except FileNotFoundError as e:
        print(f"[ERROR] Command not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during AMDGPU detection: {e}")
        sys.exit(1)


def detect_pytorch_version() -> str:
    """Auto-detect the PyTorch version from the installed package.

    Returns:
        The detected PyTorch version as major.minor (e.g., "2.7").
    """
    # Get version, remove build suffix (+rocm, +cpu, etc.) and patch version
    return version("torch").rsplit("+", 1)[0].rsplit(".", 1)[0]


def determine_root_dir(provided_root: str) -> Path:
    """Determine the TheRock root directory.

    Args:
        provided_root: User-provided root directory path, or empty string.

    Returns:
        Path object representing the TheRock root directory.
    """
    if provided_root:
        return Path(provided_root)

    # Autodetect root dir via path of the script
    # We are in <TheRock Root Dir>/external-builds/pytorch
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent.parent


def main() -> int:
    """Main entry point for the PyTorch test runner.

    Returns:
        Exit code from pytest (0 for success, non-zero for failures).
    """
    args = cmd_arguments(sys.argv[1:])

    # Determine root directory
    root_dir = determine_root_dir(args.the_rock_root_dir)

    # Determine AMDGPU family
    amdgpu_family = detect_amdgpu_family(args.amdgpu_family)
    print(f"Using AMDGPU family: {amdgpu_family}")

    # Determine PyTorch version
    pytorch_version = args.pytorch_version
    if not pytorch_version:
        pytorch_version = detect_pytorch_version()
    print(f"Using PyTorch version: {pytorch_version}")

    # Get tests to skip
    tests_to_skip = get_tests(amdgpu_family, pytorch_version, not args.debug)

    # Allow manual override of test selection
    if args.k:
        tests_to_skip = args.k

    pytorch_dir = f"{root_dir}/external-builds/pytorch/pytorch"
    setup_env(pytorch_dir)

    pytorch_args = [
        f"{pytorch_dir}/test/test_nn.py",
        f"{pytorch_dir}/test/test_torch.py",
        f"{pytorch_dir}/test/test_cuda.py",
        f"{pytorch_dir}/test/test_unary_ufuncs.py",
        f"{pytorch_dir}/test/test_binary_ufuncs.py",
        f"{pytorch_dir}/test/test_autograd.py",
        "--continue-on-collection-errors",
        "--import-mode=importlib",
        f"-k={tests_to_skip}",
        # "-n 0",  # TODO does this need rework? why should we not run this multithreaded? this does not seem to exist?
        "-v",
        # -n numprocesses, --numprocesses=numprocesses
        #         Shortcut for '--dist=load --tx=NUM*popen'.
        #         With 'logical', attempt to detect logical CPU count (requires psutil, falls back to 'auto').
        #         With 'auto', attempt to detect physical CPU count. If physical CPU count cannot be determined, falls back to 1.
        #         Forced to 0 (disabled) when used with --pdb.
    ]

    if args.no_cache:
        pytorch_args += [
            "-p",
            "no:cacheprovider",  # Disable caching: useful when running in a container
        ]

    retcode = pytest.main(pytorch_args)
    print(f"Pytest finished with return code: {retcode}")
    return retcode


if __name__ == "__main__":
    # Lets make this script return pytest exit code (success or failure)
    sys.exit(main())
