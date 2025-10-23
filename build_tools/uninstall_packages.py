#!/usr/bin/env python3
import argparse
import sys
from packaging.linux.package_load import logger
import subprocess
import os
import platform


def run_cmd(cmd):
    """Execute a shell command and return (stdout, stderr, rc)."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def detect_pkg_type():
    """Detect if system uses deb or rpm packages."""
    system = platform.system().lower()
    if system != "linux":
        logger.error("Unsupported OS: Only Linux systems are supported.")
        sys.exit(1)

    distro_id = ""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_id = line.strip().split("=")[1].strip('"').lower()
                    break

    deb_like = {"debian", "ubuntu", "mint", "pop"}
    rpm_like = {"rhel", "centos", "fedora", "rocky", "almalinux", "sles", "suse", "opensuse-leap"}

    if distro_id in deb_like:
        return "deb"
    elif distro_id in rpm_like:
        return "rpm"

    # Fallback detection
    stdout, _, _ = run_cmd("which dpkg")
    if stdout:
        return "deb"
    stdout, _, _ = run_cmd("which rpm")
    if stdout:
        return "rpm"

    logger.error("Unable to detect package manager (deb or rpm).")
    sys.exit(1)


def uninstall_by_run_id(run_id):
    """Find and uninstall packages matching the given run_id."""
    pkg_type = detect_pkg_type()
    logger.info(f"Detected package type: {pkg_type.upper()}")

    # Debian-based systems
    if pkg_type == "deb":
        cmd_list = f"dpkg -l | grep {run_id} | awk '{{print $2}}'"
        stdout, stderr, rc = run_cmd(cmd_list)
        if rc != 0 or not stdout:
            logger.info("No matching packages found for uninstall.")
            return

        pkgs = [p.strip() for p in stdout.splitlines() if p.strip()]
        logger.info(f"Found {len(pkgs)} package(s) to uninstall: {pkgs}")

        for pkg in pkgs:
            logger.info(f"Removing {pkg} ...")
            uninstall_cmd = f"sudo dpkg -r {pkg}"
            _, err, rc = run_cmd(uninstall_cmd)
            if rc == 0:
                logger.info(f"Successfully removed {pkg}")
            else:
                logger.error(f"Failed to remove {pkg}: {err}")

    # RPM-based systems
    elif pkg_type == "rpm":
        cmd_list = f"rpm -qa | grep {run_id}"
        stdout, stderr, rc = run_cmd(cmd_list)
        if rc != 0 or not stdout:
            logger.info("No matching packages found for uninstall.")
            return

        pkgs = [p.strip() for p in stdout.splitlines() if p.strip()]
        logger.info(f"Found {len(pkgs)} package(s) to uninstall: {pkgs}")

        for pkg in pkgs:
            logger.info(f"Removing {pkg} ...")
            uninstall_cmd = f"sudo rpm -e {pkg}"
            _, err, rc = run_cmd(uninstall_cmd)
            if rc == 0:
                logger.info(f"Successfully removed {pkg}")
            else:
                logger.error(f"Failed to remove {pkg}: {err}")
    else:
        logger.error("Unsupported package manager type detected.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Uninstall ROCm native build packages by run_id.")
    parser.add_argument(
        "--run_id",
        type=str,
        required=True,
        help="run_id to match installed package names (e.g., 16418185899).",
    )

    args = parser.parse_args()
    run_id = args.run_id

    logger.info("=== Starting package uninstallation ===")

    try:
        uninstall_by_run_id(run_id)
        logger.info("Uninstallation process completed.")
    except Exception as e:
        logger.error(f"Uninstallation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

