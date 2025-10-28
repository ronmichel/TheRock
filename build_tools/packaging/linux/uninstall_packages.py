#!/usr/bin/env python3
import argparse
import sys
from package_load import LoadPackages, logger
import subprocess
import os
import platform


def main():
    parser = argparse.ArgumentParser(
        description="Uninstall ROCm native build packages by run_id."
    )
    parser.add_argument(
        "--run_id",
        type=str,
        required=True,
        help="run_id to match installed package names (e.g., 16418185899).",
    )
    parser.add_argument("--package_json", required=True, help="Path to package.json.")
    parser.add_argument(
        "--version",
        choices=["true", "false"],
        default="false",
        help="If true, install only versioned packages.",
    )
    parser.add_argument(
        "--composite",
        choices=["true", "false"],
        default="false",
        help="Install composite packages only.",
    )
    parser.add_argument(
        "--amdgpu_family",
        type=str,
        required=False,
        help="Specify AMD GPU family (e.g., gfx94x).",
    )
    parser.add_argument(
        "--rocm-version",
        type=str,
        required=True,
        help="Specify ROCm version (e.g., 7.0.0).",
    )

    args = parser.parse_args()
    run_id = args.run_id

    version_flag = args.version.lower() == "true"
    composite_flag = args.composite.lower() == "true"
    amdgpu_family = args.amdgpu_family
    rocm_version = args.rocm_version

    pm = LoadPackages(args.package_json, version_flag, amdgpu_family, rocm_version)
    non_comp, comp = pm.list_composite_packages()

    # Select package list
    if composite_flag:
        logger.info(f"Count of Composite packages: {len(comp)}")
        sorted_packages = pm.sort_packages_by_dependencies(comp)
    else:
        logger.info(f"Count of non Composite packages: {len(non_comp)}")
        sorted_packages = pm.sort_packages_by_dependencies(non_comp)

    logger.info("=== Starting package uninstallation ===")

    try:
        pm.uninstall_packages(sorted_packages, composite_flag)
        logger.info("Uninstallation process completed.")
    except Exception as e:
        logger.error(f"Uninstallation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
