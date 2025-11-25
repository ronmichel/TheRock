# ROCm Package Configuration Test Suite

This test suite validates that all ROCm CMake package configurations can be found and used correctly at both build-time and install-time.

## Purpose

- Test that all CMake package configs are properly installed
- Verify packages can be found via `find_package()`
- Validate that imported targets are usable
- Test runtime functionality of ROCm libraries
- Works with both TheRock build staging directories and installed ROCm

## Components

1. **CMakeLists.txt** - Main CMake configuration
   - Tests finding all ROCm packages
   - Reports found/not found packages
   - Builds test executable if HIP is available
   - Generates test report

2. **test_main.cpp** - Runtime test application
   - Tests actual library functionality
   - Validates HIP, HSA, rocBLAS, hipBLAS, etc.
   - Reports success/failure of runtime operations

3. **test_report.txt** - Generated report
   - Summary of all tested packages
   - Configuration details
   - Search paths used

## Usage

### Testing TheRock Build (Build-Time)

Test packages from TheRock's staging directories:

```bash
# Configure test pointing to TheRock build dist directory
cd test_rocm_packages
mkdir build && cd build

cmake .. \
  -DCMAKE_PREFIX_PATH=/path/to/TheRock/build/dist/rocm \
  -DROCM_TEST_VERBOSE=ON

# Build
cmake --build .

# Run tests
ctest --verbose
# OR
./rocm_package_test
```

### Testing Installed ROCm (Install-Time)

Test packages from an installed ROCm:

```bash
# Configure test pointing to installed ROCm
cd test_rocm_packages
mkdir build-install && cd build-install

cmake .. \
  -DCMAKE_PREFIX_PATH=/opt/rocm \
  -DROCM_TEST_VERBOSE=ON

# Build
cmake --build .

# Run tests
ctest --verbose
```

### Testing Specific Package Subsets

Test only specific packages using CMAKE_PREFIX_PATH:

```bash
# Test only BLAS libraries
cmake .. \
  -DCMAKE_PREFIX_PATH="/path/to/TheRock/build/math-libs/BLAS/rocBLAS/stage;/path/to/TheRock/build/math-libs/BLAS/hipBLAS/stage"

# Test compiler packages
cmake .. \
  -DCMAKE_PREFIX_PATH="/path/to/TheRock/build/compiler/amd-llvm/stage/lib/llvm;/path/to/TheRock/build/compiler/amd-comgr/stage"
```

## CMake Options

| Option                       | Default | Description                                    |
| ---------------------------- | ------- | ---------------------------------------------- |
| `ROCM_TEST_VERBOSE`          | ON      | Print detailed find_package() results          |
| `ROCM_TEST_STRICT`           | OFF     | Fail if any package is not found               |
| `ROCM_TEST_BUILD_EXECUTABLE` | ON      | Build and test the runtime test executable     |

Example with options:

```bash
cmake .. \
  -DCMAKE_PREFIX_PATH=/opt/rocm \
  -DROCM_TEST_VERBOSE=OFF \
  -DROCM_TEST_STRICT=ON \
  -DROCM_TEST_BUILD_EXECUTABLE=ON
```

## Expected Output

### Configuration Output

```
=============================================================
ROCm Package Configuration Test
=============================================================
CMAKE_PREFIX_PATH: /opt/rocm
Testing build: /path/to/build
=============================================================

--- Testing Base Packages ---
✓ FOUND: rocm-core
  Version: 6.4.0
  Config: /opt/rocm/lib/cmake/rocm-core
✓ FOUND: rocm_smi
  Config: /opt/rocm/lib/cmake/rocm_smi
...

--- Testing Compiler Packages ---
✓ FOUND: LLVM
  Version: 19.0.0
  Config: /opt/rocm/lib/cmake/llvm
...

=============================================================
Test Summary
=============================================================
Total packages tested: 45
Packages found: 42
Packages not found: 3

Packages NOT found:
  - composable_kernel
  - hipdnn
  - miopen-plugin
=============================================================
```

### Runtime Test Output

```
========================================
ROCm Package Runtime Test
========================================

Running runtime tests...

✓ PASS: HIP: Get Device Count - Found 2 device(s)
✓ PASS: HIP: Get Device Properties - Device: AMD Radeon RX 7900 XTX
✓ PASS: HSA: Initialize
✓ PASS: rocBLAS: Create Handle
✓ PASS: rocBLAS: Get Version - Version: 4.3.0
✓ PASS: hipBLAS: Create Handle
✓ PASS: rocFFT: Get Version - Version: 1.0.31
...

========================================
Test Summary
========================================
Total tests: 15
Passed: 15
Failed: 0
========================================
```

## Integration with TheRock

### As External Test

Add to your TheRock build workflow:

```bash
# After building TheRock
cd /path/to/TheRock
cmake --build build --target therock-dist-rocm

# Run package tests
cd test_rocm_packages
mkdir build && cd build
cmake .. -DCMAKE_PREFIX_PATH=../../build/dist/rocm
cmake --build .
ctest
```

### As Subproject

You can integrate this into TheRock by adding to `tests/`:

```cmake
# In TheRock/tests/CMakeLists.txt
add_subdirectory(package_config_test)
```

## Troubleshooting

### Package Not Found

If a package isn't found:

1. Check CMAKE_PREFIX_PATH includes the correct directory
2. Verify the package's CMake config exists:
   ```bash
   find /path/to/rocm -name "*-config.cmake"
   ```
3. Check that the package was actually built:
   ```bash
   ls /path/to/TheRock/build/*/stage/lib/cmake/
   ```

### Linking Errors

If test executable fails to link:

1. Verify the library exists:
   ```bash
   find /path/to/rocm -name "lib*.so"
   ```
2. Check imported targets:
   ```cmake
   cmake .. -DROCM_TEST_VERBOSE=ON 2>&1 | grep -A5 "FOUND:"
   ```

### Runtime Errors

If test executable fails at runtime:

1. Check LD_LIBRARY_PATH includes ROCm libraries
2. Verify GPU is accessible:
   ```bash
   rocminfo
   # or
   /path/to/rocm/bin/rocminfo
   ```

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Test ROCm Packages

on: [push, pull_request]

jobs:
  test-packages:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build TheRock
        run: |
          cmake -B build -GNinja -DTHEROCK_AMDGPU_FAMILIES=gfx110X-dgpu
          cmake --build build --target therock-dist-rocm
      
      - name: Test Package Configs
        run: |
          cd test_rocm_packages
          cmake -B build -DCMAKE_PREFIX_PATH=../build/dist/rocm
          cmake --build build
          cd build && ctest --output-on-failure
```

## Advanced Usage

### Testing Single Package

```cmake
cmake_minimum_required(VERSION 3.25)
project(TestSinglePackage)

find_package(rocblas REQUIRED)

add_executable(test_rocblas test.cpp)
target_link_libraries(test_rocblas PRIVATE roc::rocblas)
```

### Custom Package Testing

You can extend the test suite by modifying `CMakeLists.txt`:

```cmake
# Add your custom package test
test_find_package(MyCustomPackage COMPONENTS component1 component2)
```

### Generating Package Dependency Graph

```bash
cmake .. -DROCM_TEST_VERBOSE=ON --graphviz=package_deps.dot
dot -Tpng package_deps.dot -o package_deps.png
```

## License

This test suite is part of TheRock project and follows the same MIT license.

## Contributing

When adding new ROCm packages to TheRock:

1. Add package test to `CMakeLists.txt` in appropriate section
2. Add runtime test to `test_main.cpp` if applicable
3. Update this README with any special configuration needed
4. Test both build-time and install-time scenarios


