#!/usr/bin/env python3

import os
import argparse
import subprocess
import boto3
import shutil
import datetime

def run_command(cmd, cwd=None):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def find_package_dir():
    """
    Finds the default output dir for packages.
    Expects packages in ./output/packages
    """
    base_dir = os.path.join(os.getcwd(), "output", "packages")
    if not os.path.exists(base_dir):
        raise RuntimeError(f"Package directory not found: {base_dir}")
    print(f"Using package directory: {base_dir}")
    return base_dir

def create_deb_repo(package_dir, origin_name):
    print("Creating APT repository...")
    dists_dir = os.path.join(package_dir, "dists", "stable", "main", "binary-amd64")
    release_dir = os.path.join(package_dir, "dists", "stable")
    pool_dir = os.path.join(package_dir, "pool", "main")

    os.makedirs(dists_dir, exist_ok=True)
    os.makedirs(pool_dir, exist_ok=True)

    for file in os.listdir(package_dir):
        if file.endswith(".deb"):
            shutil.move(os.path.join(package_dir, file), os.path.join(pool_dir, file))

    print("Generating Packages file...")
    rel_pool_path = os.path.relpath(pool_dir, dists_dir)
    cmd = f"dpkg-scanpackages pool /dev/null > Packages"
    run_command(cmd, cwd=dists_dir)

    run_command("gzip -9c Packages > Packages.gz", cwd=dists_dir)

    print("Creating Release file...")
    release_content = f"""\   
Origin: {origin_name}
Label: {origin_name}
Suite: stable
Codename: stable
Version: 1.0
Date: {datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S UTC')}
Architectures: amd64
Components: main
Description: ROCm GFX94X APT Repository (for Ubuntu 22.04/24.04)
"""
    os.makedirs(release_dir, exist_ok=True)
    release_path = os.path.join(release_dir, "Release")
    with open(release_path, "w") as f:
        f.write(release_content)
    print(f"Wrote Release file to {release_path}")


def create_rpm_repo(package_dir):
    print("Creating YUM/DNF repository...")

    arch_dir = os.path.join(package_dir, "x86_64")
    os.makedirs(arch_dir, exist_ok=True)
    for file in os.listdir(package_dir):
        if file.endswith(".rpm"):
            shutil.move(os.path.join(package_dir, file), os.path.join(arch_dir, file))
    run_command("createrepo_c .", cwd=arch_dir)
    print(f"Generated repodata/ in {arch_dir}")

def upload_to_s3(source_dir, bucket, prefix):
    s3 = boto3.client("s3")
    print(f"Uploading to s3://{bucket}/{prefix}/")

    for root, _, files in os.walk(source_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, source_dir)
            s3_key = os.path.join(prefix, rel_path).replace("\\", "/")
            print(f"Uploading: {local_path} → s3://{bucket}/{s3_key}")
            s3.upload_file(local_path, bucket, s3_key)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkg-type", required=True, choices=["deb", "rpm"], help="Type of packages to process")
    parser.add_argument("--s3-bucket", required=True, help="Target S3 bucket name")
    parser.add_argument("--amdgpu-family", required=True, help="AMDGPU family identifier (e.g., gfx94X)")
    parser.add_argument("--artifact-id", required=True, help="Unique artifact ID or version tag")
    args = parser.parse_args()

    package_dir = find_package_dir()
    s3_prefix = f"{args.amdgpu_family}_{args.artifact_id}/{args.pkg_type}"

    if args.pkg_type == "deb":
        create_deb_repo(package_dir, args.s3_bucket)
    else:
        create_rpm_repo(package_dir)

    upload_to_s3(package_dir, args.s3_bucket, s3_prefix)

if __name__ == "__main__":
    main()
