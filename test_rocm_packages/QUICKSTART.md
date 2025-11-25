# Quick Start Guide - ROCm Package Test Suite

## What This Does

This test suite validates all ROCm CMake package configurations work correctly at:
1. **Build-time**: Using TheRock's staging directories
2. **Install-time**: Using installed ROCm from `/opt/rocm` or custom location

## Quick Commands

### Test TheRock Build (Linux)

```bash
cd test_rocm_packages

# Make script executable
chmod +x run_tests.sh

# Test with TheRock build
./run_tests.sh build ../build/dist/rocm

# OR manually:
mkdir build && cd build
cmake .. -DCMAKE_PREFIX_PATH=../../build/dist/rocm
cmake --build .
./rocm_package_test
```

### Test TheRock Build (Windows)

```powershell
cd test_rocm_packages
# manually:
mkdir build
cd build
cmake .. -DCMAKE_PREFIX_PATH="..\..\build\dist\rocm"
cmake --build . --config Release
.\Release\rocm_package_test.exe
```

### Test Installed ROCm

```bash
# Linux
./run_tests.sh install /opt/rocm
```

## What Gets Tested

### Configuration Test (CMake)
Tests `find_package()` for **45+ packages**:
- ✓ Base: rocm-core, rocm-cmake, half, rocm-smi
- ✓ Compiler: LLVM, Clang, LLD, comgr, hipcc
- ✓ Runtime: HSA, HIP, HIP-lang, hiprtc
- ✓ Math: rocBLAS, hipBLAS, rocFFT, rocRAND, rocSOLVER, etc.
- ✓ ML: MIOpen, Composable Kernel
- ✓ Comm: RCCL
- ✓ Profiler: rocprofiler-sdk, roctracer

### Runtime Test (C++)
Tests actual library functionality:
- ✓ HIP device detection and properties
- ✓ HSA runtime initialization
- ✓ rocBLAS handle creation and version
- ✓ hipBLAS, rocFFT, rocRAND operations
- ✓ Library version queries

## Expected Output

```
=============================================================
ROCm Package Configuration Test
=============================================================

--- Testing Base Packages ---
✓ FOUND: rocm-core
  Version: 6.4.0
  Config: /opt/rocm/lib/cmake/rocm-core
✓ FOUND: half
✓ FOUND: rocm_smi

--- Testing Compiler Packages ---
✓ FOUND: LLVM
  Version: 19.0.0
✓ FOUND: Clang
✓ FOUND: amd_comgr

--- Testing Runtime Packages ---
✓ FOUND: hip
✓ FOUND: hsa-runtime64

--- Testing Math Packages ---
✓ FOUND: rocblas
✓ FOUND: rocfft
✓ FOUND: rocrand

=============================================================
Test Summary
=============================================================
Total packages tested: 45
Packages found: 42
Packages not found: 3
```

Then runtime tests:

```
========================================
ROCm Package Runtime Test
========================================

✓ PASS: HIP: Get Device Count - Found 1 device(s)
✓ PASS: HIP: Get Device Properties - Device: AMD Radeon RX 7900 XTX
✓ PASS: HSA: Initialize
✓ PASS: rocBLAS: Create Handle
✓ PASS: rocBLAS: Get Version - Version: 4.3.0
✓ PASS: rocFFT: Get Version - Version: 1.0.31

========================================
Test Summary
========================================
Total tests: 8
Passed: 8
Failed: 0
========================================
```

## Files Created

| File                  | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `CMakeLists.txt`      | Main test configuration, finds all packages          |
| `test_main.cpp`       | Runtime test application                             |
| `test_report.txt.in`  | Generated test report template                       |
| `README.md`           | Detailed documentation                               |
| `QUICKSTART.md`       | This file - quick reference                          |
| `run_tests.sh`        | Automated test runner (Linux)                        |

## Common Use Cases

### 1. Validate TheRock Build

After building TheRock, verify all packages are configured correctly:

```bash
# Build TheRock
cd TheRock
cmake -B build -DTHEROCK_AMDGPU_FAMILIES=gfx110X-dgpu
cmake --build build --target therock-dist-rocm

# Test packages
cd test_rocm_packages
./run_tests.sh build ../build/dist/rocm
```

### 2. Verify Installation

After installing ROCm, verify it's properly configured:

```bash
# Install ROCm
cd TheRock/build
cmake --install . --prefix /opt/rocm

# Test installation
cd ../test_rocm_packages
./run_tests.sh install /opt/rocm
```

### 3. Debug Missing Package

Find out why a specific package isn't found:

```bash
cd test_rocm_packages
mkdir debug && cd debug

# Verbose output
cmake .. \
  -DCMAKE_PREFIX_PATH=/opt/rocm \
  -DROCM_TEST_VERBOSE=ON \
  --debug-find 2>&1 | tee cmake_debug.log

# Search for specific package in log
grep -A10 "find_package(rocblas)" cmake_debug.log
```

### 4. Test Specific Packages Only

Modify CMakeLists.txt to test only what you need:

```cmake
# Comment out sections you don't need
# test_find_package(rocblas)
# test_find_package(hipblas)
```

Or point to specific staging directories:

```bash
cmake .. -DCMAKE_PREFIX_PATH="/path/to/rocBLAS/stage;/path/to/hipBLAS/stage"
```

### 5. CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test-packages.yml
- name: Test ROCm Packages
  run: |
    cd test_rocm_packages
    ./run_tests.sh build ../build/dist/rocm
```

## Troubleshooting

### "Package not found"

1. Verify path exists:
   ```bash
   ls -la /opt/rocm/lib/cmake/
   ```

2. Check for config file:
   ```bash
   find /opt/rocm -name "rocblas-config.cmake"
   ```

3. Try with absolute path:
   ```bash
   cmake .. -DCMAKE_PREFIX_PATH="/absolute/path/to/rocm"
   ```

### "Cannot find headers"

CMake found the package but compilation fails:

```bash
# Check include directories
grep -r "INTERFACE_INCLUDE_DIRECTORIES" /opt/rocm/lib/cmake/rocblas/
```

### "Linking errors"

Package found but linking fails:

```bash
# Verify library exists
find /opt/rocm -name "librocblas.so*"

# Check RPATH
readelf -d ./rocm_package_test | grep RPATH
```

### Runtime failures

Test executable crashes:

```bash
# Check library dependencies
ldd ./rocm_package_test

# Set library path
export LD_LIBRARY_PATH=/opt/rocm/lib:$LD_LIBRARY_PATH
./rocm_package_test
```

## Advanced Usage

### Test with Different CMake Versions

```bash
cmake --version  # Check current version

# Use specific CMake
/path/to/cmake-3.28/bin/cmake ..
```

### Generate Dependency Graph

```bash
cmake .. --graphviz=package_deps.dot
dot -Tpng package_deps.dot -o deps.png
```

### Test in Docker

```dockerfile
FROM ubuntu:22.04
COPY test_rocm_packages /test
WORKDIR /test
RUN apt-get update && apt-get install -y cmake ninja-build
CMD ["./run_tests.sh", "install", "/opt/rocm"]
```

## Next Steps

- See [README.md](README.md) for detailed documentation
- Check [test_main.cpp](test_main.cpp) to add custom runtime tests
- Modify [CMakeLists.txt](CMakeLists.txt) to test additional packages
- Review generated `build/test_report.txt` for detailed results

## Support

For issues or questions:
1. Check the detailed README.md
2. Review TheRock documentation at https://github.com/ROCm/TheRock
3. Check CMAKE_PREFIX_PATH and package installation
4. Enable verbose mode: `-DROCM_TEST_VERBOSE=ON`


