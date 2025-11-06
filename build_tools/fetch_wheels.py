#!/usr/bin/env python3
"""
Download .whl files from a CloudFront URL amdgpu_family into a specified directory.

USAGE:
    python download_from_cloudfront.py \
        --cloudfront_url ${PACKAGE_INDEX_URL} \
        --amdgpu_family ${amdgpu_family} \
        --dir ${WHEELHOUSE_DIR} \
        --list_whls '["jax_pjrt.whl","jax_plugin.whl","jaxlib.whl"]'

EXAMPLE:
    python download_from_cloudfront.py \
        --cloudfront_url https://rocm.nightlies.amd.com/v2-staging  \
        --amdgpu_family gfx94X-dcgpu \
        --dir wheelhouse \
        --list_whls '["jax_pjrt.whl","jax_plugin.whl","jaxlib.whl"]'

This will:
    - Create wheelhouse if it does not exist.
    - Download:
        https://rocm.nightlies.amd.com/v2-staging/gfx94X-dcgpu/jax_pjrt.whl
        https://rocm.nightlies.amd.com/v2-staging/gfx94X-dcgpu/jax_plugin.whl
        https://rocm.nightlies.amd.com/v2-staging/gfx94X-dcgpu/jaxlib.whl
    - Save all files into wheelhouse
"""

import os
import subprocess
import argparse
import ast
import logging
from urllib.parse import quote
from github_actions.github_actions_utils import gha_append_step_summary

# Configure logging
log = logging.getLogger(__name__)

def download_files(cloudfront_url, amdgpu_family, whl_list, wheelhouse_dir):
    # Create the wheelhouse directory if it doesn't exist
    os.makedirs(wheelhouse_dir, exist_ok=True)

    # Download each wheel file
    for whl_file_name in whl_list:
        encoded_filename = quote(whl_file_name, safe='')
        full_url = f"{cloudfront_url.rstrip('/')}/{amdgpu_family.strip('/')}/{encoded_filename}"
        log.info(f"Downloading: {whl_file_name}")
        log.info(f"Encoded URL: {full_url}")

        wget_cmd = ["wget", "-P", wheelhouse_dir, full_url]
        log.info(f"Running command: {' '.join(wget_cmd)}")

        try:
            subprocess.run(wget_cmd, check=True)
            log.info(f"Downloaded {whl_file_name} -> {wheelhouse_dir}")
            gha_append_step_summary(f"Downloaded {whl_file_name} -> {wheelhouse_dir}")
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to download {whl_file_name}")
            log.error(f"Error: {e}")
            gha_append_step_summary(f"Failed to download {whl_file_name}")

def main():
    parser = argparse.ArgumentParser(
        description="Download wheel files from a CloudFront URL amdgpu_family into a target directory."
    )
    parser.add_argument("--cloudfront_url", required=True, help="Base CloudFront URL.")
    parser.add_argument("--amdgpu_family", required=True, help="Subamdgpu_family inside the CloudFront distribution.")
    parser.add_argument("--dir", required=True, dest="wheelhouse_dir", help="Directory to save downloaded wheels.")
    parser.add_argument(
        "--list_whls",
        required=True,
        help="list of wheel filenames, e.g. '["jax_pjrt.whl","jax_plugin.whl","jaxlib.whl"]'"
    )

    args = parser.parse_args()

    try:
        whl_list = ast.literal_eval(args.list_whls)
        if not isinstance(whl_list, list):
            raise ValueError
    except Exception:
        log.error("Error: --list_whls must be a valid Python list, e.g. '["jax_pjrt.whl","jax_plugin.whl","jaxlib.whl"]'")
        exit(1)

    log.info("Parsed arguments:")
    log.info(f"CLOUDFRONT_URL: {args.cloudfront_url}")
    log.info(f"AMDGPU_FAMILY: {args.amdgpu_family}")
    log.info(f"OUTPUT_DIR: {args.wheelhouse_dir}")
    log.info(f"FILES: {whl_list}")

    download_files(args.cloudfront_url, args.amdgpu_family, whl_list, args.wheelhouse_dir)

if __name__ == "__main__":
    main()
