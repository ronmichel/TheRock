# Example Dockerfile for PyTorch with ROCm support
FROM ubuntu:24.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip git wget curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables (example values, replace as needed)
ENV PYTHON_VERSION=3.12
ENV TORCH_VERSION=2.3.0
ENV ROCM_VERSION=6.2
ENV PACKAGE_INDEX_URL=https://d25kgig7rdsyks.cloudfront.net/v2-staging
ENV AMDGPU_FAMILY=gfx94X-dcgpu

# Install PyTorch (example, adjust as needed)
RUN pip3 install torch==${TORCH_VERSION} --extra-index-url ${PACKAGE_INDEX_URL}

# Add your additional build steps here
