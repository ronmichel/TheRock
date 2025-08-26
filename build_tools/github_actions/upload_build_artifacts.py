#!/usr/bin/env python3
"""
upload_build_artifacts.py

Uploads build artifacts to AWS S3 bucket
"""

import argparse
import logging
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys

logging.basicConfig(level=logging.INFO)

THEROCK_DIR = Path(__file__).resolve().parent.parent.parent
PLATFORM = platform.system().lower()

# Importing indexer.py
sys.path.append(str(THEROCK_DIR / "third-party" / "indexer"))
from indexer import process_dir


def exec(cmd: list[str], cwd: Path):
    logging.info(f"++ Exec [{cwd}]$ {shlex.join(cmd)}")
    subprocess.run(cmd, check=True)


def retrieve_bucket_info() -> tuple[str, str]:
    github_repository = os.getenv("GITHUB_REPOSITORY", "ROCm/TheRock")
    is_pr_from_fork = os.getenv("IS_PR_FROM_FORK", "false") == "true"
    owner, repo_name = github_repository.split("/")
    external_repo = (
        ""
        if repo_name == "TheRock" and owner == "ROCm" and not is_pr_from_fork
        else f"{owner}-{repo_name}/"
    )
    bucket = (
        "therock-artifacts"
        if repo_name == "TheRock" and owner == "ROCm" and not is_pr_from_fork
        else "therock-artifacts-external"
    )
    return (external_repo, bucket)


def create_index_file(args: argparse.Namespace):
    logging.info("Creating index file")
    build_dir = args.build_dir / "artifacts"

    indexer_args = argparse.Namespace()
    indexer_args.filter = ["*.tar.xz*"]
    indexer_args.output_file = "index.html"
    indexer_args.verbose = False
    indexer_args.recursive = False
    process_dir(build_dir, indexer_args)


## Enhancement to upload HTML test report to built artifacts dir
def upload_test_report(report_path: Path, bucket_uri: str):
    """Upload the HTML test report as multi_node_test_report.html under bucket_uri."""
    if not report_path.exists():
        logging.warning("Test report not found at %s — skipping upload.", report_path)
        return

    dest = f"{bucket_uri}/multi_node_test_report.html"
    logging.info("Uploading test report: %s -> %s", report_path, dest)

    # Content-Type helps browsers render HTML directly from S3 if public / through proxy
    cmd = [
        "aws",
        "s3",
        "cp",
        str(report_path),
        dest,
        "--content-type",
        "text/html",
    ]
    exec(cmd, cwd=Path.cwd())


def upload_artifacts(args: argparse.Namespace, bucket_uri: str):
    logging.info("Uploading artifacts to S3")
    build_dir = args.build_dir
    amdgpu_family = args.amdgpu_family

    # Uploading artifacts to S3 bucket
    cmd = [
        "aws",
        "s3",
        "cp",
        str(build_dir / "artifacts"),
        bucket_uri,
        "--recursive",
        "--no-follow-symlinks",
        "--exclude",
        "*",
        "--include",
        "*.tar.xz*",
    ]
    exec(cmd, cwd=Path.cwd())

    # Uploading index.html to S3 bucket
    cmd = [
        "aws",
        "s3",
        "cp",
        str(build_dir / "artifacts" / "index.html"),
        f"{bucket_uri}/index-{amdgpu_family}.html",
    ]
    exec(cmd, cwd=Path.cwd())


def run(args: argparse.Namespace):
    external_repo_path, bucket = retrieve_bucket_info()
    run_id = args.run_id
    bucket_uri = f"s3://{bucket}/{external_repo_path}{run_id}-{PLATFORM}"
    if args.upload_report:
        logging.info(
            "--upload-report is set; uploading rccl-tests  from {args.report_path} on runner to f'{bucket_uri}/multi_node_test_report.html'"
        )
        upload_test_report(args.report_path, bucket_uri)
    else:
        create_index_file(args)
        upload_artifacts(args, bucket_uri)


def main(argv):
    parser = argparse.ArgumentParser(prog="artifact_upload")
    parser.add_argument(
        "--run-id", type=str, required=True, help="GitHub run ID of this workflow run"
    )

    parser.add_argument(
        "--amdgpu-family", type=str, required=True, help="AMD GPU family to upload"
    )

    parser.add_argument(
        "--build-dir",
        type=Path,
        required=True,
        help="Path to the build directory of TheRock",
    )

    # Path to the test report we want to upload as multi_node_test_report.html
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("/var/www/html/cvs/ci_test_report.html"),
        help="Path to the HTML test report to upload as multi_node_test_report.html",
    )

    parser.add_argument(
        "--upload-report",
        action="store_true",  # flips to True if the flag is provided
        default=False,  # default is False when flag is omitted
        help="Upload rccl-tests report as multi_node_test_report.html",
    )

    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main(sys.argv[1:])
