# TheRock: Build-Time CMake Configuration File Paths

## Overview

This document provides a comprehensive mapping of all packages in TheRock to their build-time CMake configuration file paths. This is essential for understanding the build system structure and debugging build issues.
---

## Table of Contents

1. [Build System Architecture](#build-system-architecture)
2. [Directory Structure](#directory-structure)
3. [Complete Package-to-CMake-Config Mapping](#complete-package-to-cmake-config-mapping)
4. [Build-Time Path Resolution](#build-time-path-resolution)
5. [CMake Package Discovery](#cmake-package-discovery)

---

## Build System Architecture

### Subproject Build Stages

TheRock uses a multi-stage build system managed by `therock_cmake_subproject_declare()`:

1. **Configure Stage**: CMake configures the subproject
   - Output: `<subproject>/build/CMakeCache.txt`
   - Stamp: `<subproject>/stamp/configure.stamp`

2. **Build Stage**: Project is compiled
   - Working dir: `<subproject>/build/`
   - Stamp: `<subproject>/stamp/build.stamp`

3. **Stage Install**: Installation to staging directory
   - Target: `CMAKE_INSTALL_PREFIX=<subproject>/stage/`
   - Stamp: `<subproject>/stamp/stage.stamp`
   - **CMake configs install here**: `<subproject>/stage/lib/cmake/<package>/`

4. **Dist**: Flattened distribution directory
   - Location: `<subproject>/dist/`
   - Combined with transitive dependencies

5. **Artifact**: Organized by component type
   - Location: `build/artifacts/<artifact>_<component>_<target>/`
   - Sourced from all relevant stage directories

### Key CMake Variables

During subproject configuration:
- `CMAKE_INSTALL_PREFIX=${_stage_destination_dir}` 
  - Usually: `<subproject>/stage/`
  - With INSTALL_DESTINATION: `<subproject>/stage/${INSTALL_DESTINATION}`
- `THEROCK_STAGE_INSTALL_ROOT=${_stage_dir}` - Root staging directory

---

## Directory Structure

### Standard Subproject Layout

```
<component>/<subproject>/
├── build/                      # CMake build directory
│   ├── CMakeCache.txt
│   ├── cmake_install.cmake
│   └── compile_commands.json
├── stage/                      # Installation staging directory
│   ├── lib/
│   │   ├── cmake/             # ← CMake configs install here
│   │   │   └── <package>/
│   │   │       ├── <package>-config.cmake
│   │   │       ├── <package>-config-version.cmake
│   │   │       └── <package>-targets.cmake
│   │   ├── lib<name>.so       # Shared libraries
│   │   └── pkgconfig/
│   ├── include/               # Header files
│   ├── bin/                   # Executables
│   └── share/                 # Documentation, data files
├── dist/                      # Flattened distribution
│   └── (combined with deps)
├── stamp/                     # Build stamps
│   ├── configure.stamp
│   ├── build.stamp
│   └── stage.stamp
└── prefix/                    # (internal use)
```

### Special Cases

#### LLVM (amd-llvm)

```
compiler/amd-llvm/
└── stage/
    └── lib/
        └── llvm/              # INSTALL_DESTINATION="lib/llvm"
            ├── bin/
            ├── lib/
            │   └── cmake/
            │       ├── AMDDeviceLibs/
            │       ├── clang/
            │       ├── lld/
            │       └── llvm/
            └── amdgcn/
```

#### Overlay Packages (aux-overlay)

Pre-installed CMake configs that overlay the LLVM installation:

```
base/aux-overlay/
└── stage/
    └── lib/
        └── cmake/
            ├── AMDDeviceLibs/  # Overlay for AMDDeviceLibs
            ├── clang/           # Overlay for Clang
            ├── lld/             # Overlay for LLD
            └── llvm/            # Overlay for LLVM
```

---

## Complete Package-to-CMake-Config Mapping

### Base Packages

#### 1. rocm-cmake

**Subproject**: `base/rocm-cmake`  
**CMake Packages Provided**:
- **ROCmCMakeBuildTools**
  - Path: `base/rocm-cmake/stage/share/rocmcmakebuildtools/cmake/`
  - Files:
    - Multiple `.cmake` module files
    - Utilities for ROCm package configuration

- **ROCM**
  - Path: `base/rocm-cmake/stage/share/rocm/cmake/`
  - Files:
    - `rocm-config.cmake`
    - `rocm-config-version.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(rocm-cmake
  ROCmCMakeBuildTools share/rocmcmakebuildtools/cmake)
therock_cmake_subproject_provide_package(rocm-cmake
  ROCM share/rocm/cmake)
```

#### 2. rocm-core

**Subproject**: `base/rocm-core`  
**Build Dir**: `base/rocm-core/build/`  
**Stage Dir**: `base/rocm-core/stage/`

**CMake Package**: rocm-core  
**Config Path**: `base/rocm-core/stage/lib/cmake/rocm-core/`

**Files**:
- `rocm-core-config.cmake`
- `rocm-core-config-version.cmake`
- `rocm-core-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(rocm-core rocm-core lib/cmake/rocm-core)
```

#### 3. amd-smi (amdsmi)

**Subproject**: `base/amdsmi`  
**Stage Dir**: `base/amdsmi/stage/`

**CMake Package**: amd_smi  
**Config Path**: `base/amdsmi/stage/lib/cmake/amd_smi/`

**Files**:
- `amd_smi-config.cmake`
- `amd_smi-config-version.cmake`
- `amd_smi-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(amdsmi
  amd_smi lib/cmake)
```

#### 4. rocm-smi-lib (rocm_smi_lib)

**Subproject**: `base/rocm_smi_lib`  
**Stage Dir**: `base/rocm_smi_lib/stage/`

**CMake Package**: rocm_smi  
**Config Path**: `base/rocm_smi_lib/stage/lib/cmake/rocm_smi/`

**Files**:
- `rocm_smi-config.cmake`
- `rocm_smi-config-version.cmake`
- `rocm_smi-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(rocm_smi_lib rocm_smi lib/cmake/rocm_smi)
```

#### 5. rocprofiler-register

**Subproject**: `base/rocprofiler-register`  
**Stage Dir**: `base/rocprofiler-register/stage/`

**CMake Package**: rocprofiler-register  
**Config Path**: `base/rocprofiler-register/stage/lib/cmake/rocprofiler-register/`

**Files**:
- `rocprofiler-register-config.cmake`
- `rocprofiler-register-config-version.cmake`
- `rocprofiler-register-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(rocprofiler-register
  rocprofiler-register lib/cmake/rocprofiler-register)
```

#### 6. half (rocm-half)

**Subproject**: `base/half`  
**Stage Dir**: `base/half/stage/`

**CMake Package**: half  
**Config Path**: `base/half/stage/lib/cmake/half/`

**Files**:
- `half-config.cmake`
- `half-config-version.cmake`
- `half-targets.cmake`

**Note**: Header-only library, no explicit package declaration but CMake configs are installed by the half project itself.

---

### Compiler Packages

#### 7. amd-llvm

**Subproject**: `compiler/amd-llvm`  
**Build Dir**: `compiler/amd-llvm/build/`  
**Stage Dir**: `compiler/amd-llvm/stage/`  
**Install Destination**: `lib/llvm` (special case)

**Effective Stage Path**: `compiler/amd-llvm/stage/lib/llvm/`

**CMake Packages Provided**:

##### 7a. LLVM
**Config Path**: `compiler/amd-llvm/stage/lib/llvm/lib/cmake/llvm/`

**Files**:
- `LLVMConfig.cmake`
- `LLVMConfigVersion.cmake`
- `LLVMExports.cmake`
- `LLVMExports-*.cmake` (per build type)
- Multiple component configs

**Overlay Path**: `base/aux-overlay/stage/lib/cmake/llvm/`
- `LLVMConfig.cmake` (overlay)
- `LLVMConfigVersion.cmake` (overlay)

##### 7b. Clang
**Config Path**: `compiler/amd-llvm/stage/lib/llvm/lib/cmake/clang/`

**Files**:
- `ClangConfig.cmake`
- `ClangConfigVersion.cmake`
- `ClangTargets.cmake`

**Overlay Path**: `base/aux-overlay/stage/lib/cmake/clang/`
- `ClangConfig.cmake` (overlay)
- `ClangConfigVersion.cmake` (overlay)

##### 7c. LLD
**Config Path**: `compiler/amd-llvm/stage/lib/llvm/lib/cmake/lld/`

**Files**:
- `LLDConfig.cmake`
- `LLDConfigVersion.cmake`
- `LLDTargets.cmake`

**Overlay Path**: `base/aux-overlay/stage/lib/cmake/lld/`
- `LLDConfig.cmake` (overlay)
- `LLDConfigVersion.cmake` (overlay)

##### 7d. AMDDeviceLibs
**Config Path**: `compiler/amd-llvm/stage/lib/llvm/lib/cmake/AMDDeviceLibs/`

**Files**:
- `AMDDeviceLibsConfig.cmake`

**Overlay Path**: `base/aux-overlay/stage/lib/cmake/AMDDeviceLibs/`
- `AMDDeviceLibsConfig.cmake` (overlay)

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(amd-llvm AMDDeviceLibs lib/llvm/lib/cmake/AMDDeviceLibs)
therock_cmake_subproject_provide_package(amd-llvm Clang lib/llvm/lib/cmake/clang)
therock_cmake_subproject_provide_package(amd-llvm LLD lib/llvm/lib/cmake/lld)
therock_cmake_subproject_provide_package(amd-llvm LLVM lib/llvm/lib/cmake/llvm)
```

#### 8. amd-comgr

**Subproject**: `compiler/amd-comgr` (or `amd-comgr-impl` if delay-load enabled)  
**Stage Dir**: `compiler/amd-comgr/stage/`

**CMake Package**: amd_comgr  
**Config Path**: `compiler/amd-comgr/stage/lib/cmake/amd_comgr/`

**Files**:
- `amd_comgr-config.cmake`
- `amd_comgr-config-version.cmake`
- `amd_comgr-targets.cmake`

**Declaration** (when NOT delay-load):
```cmake
therock_cmake_subproject_provide_package(amd-comgr amd_comgr lib/cmake/amd_comgr)
```

#### 9. amd-comgr-stub

**Subproject**: `compiler/amd-comgr-stub`  
**Stage Dir**: `compiler/amd-comgr-stub/stage/`

**CMake Package**: amd_comgr (via stub)  
**Config Path**: `compiler/amd-comgr-stub/stage/lib/cmake/amd_comgr_stub/`

**Files**:
- `amd_comgr_stub-config.cmake`
- `amd_comgr_stub-targets.cmake`

**Declaration** (when delay-load enabled):
```cmake
therock_cmake_subproject_provide_package(amd-comgr-stub amd_comgr lib/cmake/amd_comgr_stub)
```

**Note**: When delay-load is enabled, this provides the `amd_comgr` package instead of the main amd-comgr subproject.

#### 10. hipcc

**Subproject**: `compiler/hipcc`  
**Stage Dir**: `compiler/hipcc/stage/`

**CMake Package**: hipcc  
**Config Path**: `compiler/hipcc/stage/lib/cmake/hipcc/`

**Files**:
- `hipcc-config.cmake`
- `hipcc-targets.cmake`

**Note**: No explicit package declaration, but CMake configs installed by hipcc project.

#### 11. hipify

**Subproject**: `compiler/hipify`  
**Stage Dir**: `compiler/hipify/stage/`

**CMake Package**: hipify (if provided)  
**Config Path**: `compiler/hipify/stage/lib/cmake/hipify/`

**Note**: No explicit package declaration in shown code. Check hipify project for configs.

---

### Core Runtime Packages

#### 12. ROCR-Runtime

**Subproject**: `core/ROCR-Runtime`  
**Build Dir**: `core/ROCR-Runtime/build/`  
**Stage Dir**: `core/ROCR-Runtime/stage/`

**CMake Packages Provided**:

##### 12a. hsa-runtime64
**Config Path**: `core/ROCR-Runtime/stage/lib/cmake/hsa-runtime64/`

**Files**:
- `hsa-runtime64-config.cmake`
- `hsa-runtime64-config-version.cmake`
- `hsa-runtime64-targets.cmake`

##### 12b. hsakmt
**Config Path**: `core/ROCR-Runtime/stage/lib/cmake/hsakmt/`

**Files**:
- `hsakmt-config.cmake`
- `hsakmt-config-version.cmake`
- `hsakmt-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(ROCR-Runtime hsakmt lib/cmake/hsakmt)
therock_cmake_subproject_provide_package(ROCR-Runtime hsa-runtime64 lib/cmake/hsa-runtime64)
```

#### 13. rocminfo

**Subproject**: `core/rocminfo`  
**Stage Dir**: `core/rocminfo/stage/`

**CMake Package**: rocminfo (if provided)  
**Config Path**: `core/rocminfo/stage/lib/cmake/rocminfo/` (if exists)

**Note**: Primarily a utility binary. May not provide CMake configs.

---

### HIP Runtime Packages

#### 14. hip-clr

**Subproject**: `core/hip-clr`  
**Build Dir**: `core/clr/build/`  
**Stage Dir**: `core/clr/stage/`

**CMake Packages Provided**:

##### 14a. hip / HIP
**Config Path**: `core/clr/stage/lib/cmake/hip/`

**Files**:
- `hip-config.cmake`
- `hip-config-version.cmake`
- `hip-targets.cmake`
- `hip-targets-*.cmake` (per build type)

##### 14b. hip-lang
**Config Path**: `core/clr/stage/lib/cmake/hip-lang/`

**Files**:
- `hip-lang-config.cmake`
- `hip-lang-config-version.cmake`
- `hip-lang-targets.cmake`

##### 14c. hiprtc
**Config Path**: `core/clr/stage/lib/cmake/hiprtc/`

**Files**:
- `hiprtc-config.cmake`
- `hiprtc-config-version.cmake`
- `hiprtc-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(hip-clr hip lib/cmake/hip)
therock_cmake_subproject_provide_package(hip-clr HIP lib/cmake/hip)  # Alias
therock_cmake_subproject_provide_package(hip-clr hip-lang lib/cmake/hip-lang)
therock_cmake_subproject_provide_package(hip-clr hiprtc lib/cmake/hiprtc)
```

#### 15. ocl-clr

**Subproject**: `core/ocl-clr`  
**Build Dir**: `core/ocl-clr/build/`  
**Stage Dir**: `core/ocl-clr/stage/`

**CMake Package**: ocl-icd  
**Config Path**: `core/ocl-clr/stage/lib/cmake/ocl-icd/`

**Files**:
- `ocl-icd-config.cmake`
- `ocl-icd-targets.cmake`

**Declaration**:
```cmake
therock_cmake_subproject_provide_package(ocl-clr ocl-icd lib/cmake/ocl-icd)
```

---

### Math Libraries - Pattern

All math libraries follow the same pattern. Based on the CMakeLists.txt structure, here's the general format:

#### General Math Library Pattern

**Subproject Location**: `math-libs/<category>/<library>/`  
**Build Dir**: `math-libs/<category>/<library>/build/`  
**Stage Dir**: `math-libs/<category>/<library>/stage/`  
**CMake Config Path**: `math-libs/<category>/<library>/stage/lib/cmake/<package>/`

**Config Files**:
- `<package>-config.cmake`
- `<package>-config-version.cmake`
- `<package>-targets.cmake`

### PRIM Libraries

#### 16. rocPRIM

**Subproject**: `math-libs/rocPRIM`  
**CMake Package**: rocprim  
**Config Path**: `math-libs/rocPRIM/stage/lib/cmake/rocprim/`

#### 17. hipCUB

**Subproject**: `math-libs/hipCUB`  
**CMake Package**: hipcub  
**Config Path**: `math-libs/hipCUB/stage/lib/cmake/hipcub/`

#### 18. rocThrust

**Subproject**: `math-libs/rocThrust`  
**CMake Package**: rocthrust  
**Config Path**: `math-libs/rocThrust/stage/lib/cmake/rocthrust/`

### RAND Libraries

#### 19. rocRAND

**Subproject**: `math-libs/rocRAND`  
**CMake Package**: rocrand  
**Config Path**: `math-libs/rocRAND/stage/lib/cmake/rocrand/`

#### 20. hipRAND

**Subproject**: `math-libs/hipRAND`  
**CMake Package**: hiprand  
**Config Path**: `math-libs/hipRAND/stage/lib/cmake/hiprand/`

### FFT Libraries

#### 21. rocFFT

**Subproject**: `math-libs/rocFFT`  
**CMake Package**: rocfft  
**Config Path**: `math-libs/rocFFT/stage/lib/cmake/rocfft/`

#### 22. hipFFT

**Subproject**: `math-libs/hipFFT`  
**CMake Package**: hipfft  
**Config Path**: `math-libs/hipFFT/stage/lib/cmake/hipfft/`

### BLAS Libraries

#### 23. rocBLAS

**Subproject**: `math-libs/BLAS/rocBLAS`  
**CMake Package**: rocblas  
**Config Path**: `math-libs/BLAS/rocBLAS/stage/lib/cmake/rocblas/`

#### 24. hipBLAS

**Subproject**: `math-libs/BLAS/hipBLAS`  
**CMake Package**: hipblas  
**Config Path**: `math-libs/BLAS/hipBLAS/stage/lib/cmake/hipblas/`

#### 25. hipBLASLt

**Subproject**: `math-libs/BLAS/hipBLASLt`  
**CMake Package**: hipblaslt  
**Config Path**: `math-libs/BLAS/hipBLASLt/stage/lib/cmake/hipblaslt/`

#### 26. hipBLAS-common

**Subproject**: `math-libs/BLAS/hipBLAS-common`  
**CMake Package**: hipblas-common  
**Config Path**: `math-libs/BLAS/hipBLAS-common/stage/lib/cmake/hipblas-common/`

### SPARSE Libraries

#### 27. rocSPARSE

**Subproject**: `math-libs/BLAS/rocSPARSE`  
**CMake Package**: rocsparse  
**Config Path**: `math-libs/BLAS/rocSPARSE/stage/lib/cmake/rocsparse/`

#### 28. hipSPARSE

**Subproject**: `math-libs/BLAS/hipSPARSE`  
**CMake Package**: hipsparse  
**Config Path**: `math-libs/BLAS/hipSPARSE/stage/lib/cmake/hipsparse/`

#### 29. hipSPARSELt

**Subproject**: `math-libs/BLAS/hipSPARSELt`  
**CMake Package**: hipsparselt  
**Config Path**: `math-libs/BLAS/hipSPARSELt/stage/lib/cmake/hipsparselt/`

### SOLVER Libraries

#### 30. rocSOLVER

**Subproject**: `math-libs/BLAS/rocSOLVER`  
**CMake Package**: rocsolver  
**Config Path**: `math-libs/BLAS/rocSOLVER/stage/lib/cmake/rocsolver/`

#### 31. hipSOLVER

**Subproject**: `math-libs/BLAS/hipSOLVER`  
**CMake Package**: hipsolver  
**Config Path**: `math-libs/BLAS/hipSOLVER/stage/lib/cmake/hipsolver/`

---

### ML Libraries

#### 32. MIOpen

**Subproject**: `ml-libs/MIOpen`  
**CMake Package**: miopen  
**Config Path**: `ml-libs/MIOpen/stage/lib/cmake/miopen/`

**Files**:
- `miopen-config.cmake`
- `miopen-config-version.cmake`
- `miopen-targets.cmake`

#### 33. Composable Kernel

**Subproject**: `ml-libs/composable_kernel`  
**CMake Package**: composable_kernel  
**Config Path**: `ml-libs/composable_kernel/stage/lib/cmake/composable_kernel/`

**Files**:
- `composable_kernel-config.cmake`
- `composable_kernel-config-version.cmake`
- `composable_kernel-targets.cmake`

#### 34. hipDNN

**Subproject**: `ml-libs/hipDNN`  
**CMake Package**: hipdnn  
**Config Path**: `ml-libs/hipDNN/stage/lib/cmake/hipdnn/`

#### 35. MIOpen Plugin

**Subproject**: `ml-libs/MIOpen/plugin`  
**CMake Package**: miopen-plugin  
**Config Path**: `ml-libs/MIOpen/plugin/stage/lib/cmake/miopen-plugin/`

---

### Communication Libraries

#### 36. RCCL

**Subproject**: `comm-libs/rccl`  
**CMake Package**: rccl  
**Config Path**: `comm-libs/rccl/stage/lib/cmake/rccl/`

**Files**:
- `rccl-config.cmake`
- `rccl-config-version.cmake`
- `rccl-targets.cmake`

---

### Profiler Libraries

#### 37. rocprofiler-sdk

**Subproject**: `profiler/rocprofiler-sdk`  
**CMake Package**: rocprofiler-sdk  
**Config Path**: `profiler/rocprofiler-sdk/stage/lib/cmake/rocprofiler-sdk/`

**Files**:
- `rocprofiler-sdk-config.cmake`
- `rocprofiler-sdk-config-version.cmake`
- `rocprofiler-sdk-targets.cmake`

#### 38. roctracer

**Subproject**: `profiler/roctracer`  
**CMake Package**: roctracer  
**Config Path**: `profiler/roctracer/stage/lib/cmake/roctracer/`

**Files**:
- `roctracer-config.cmake`
- `roctracer-config-version.cmake`
- `roctracer-targets.cmake`

#### 39. hsa-amd-aqlprofile

**Subproject**: `profiler/aqlprofile`  
**CMake Package**: hsa-amd-aqlprofile  
**Config Path**: `profiler/aqlprofile/stage/lib/cmake/hsa-amd-aqlprofile/`

**Files**:
- `hsa-amd-aqlprofile-config.cmake`
- `hsa-amd-aqlprofile-targets.cmake`

---

### Third-Party/Support Libraries

These are bundled dependencies that also provide CMake configs:

#### 40. bzip2

**Config Path**: `third-party/sysdeps/common/bzip2/stage/lib/cmake/bzip2/`  
**Config Template**: `third-party/sysdeps/common/bzip2/bzip2-config.cmake.in`

#### 41. zlib

**Config Path**: `third-party/sysdeps/common/zlib/stage/lib/cmake/zlib/`  
**Config Template**: `third-party/sysdeps/common/zlib/zlib-config.cmake.in`

#### 42. zstd

**Config Path**: `third-party/sysdeps/common/zstd/stage/lib/cmake/zstd/`  
**Config Template**: `third-party/sysdeps/common/zstd/zstd-config.cmake.in`

#### 43. liblzma

**Config Path**: `third-party/sysdeps/common/liblzma/stage/lib/cmake/liblzma/`  
**Config Template**: `third-party/sysdeps/common/liblzma/liblzma-config.cmake.in`

#### 44. sqlite3

**Config Path**: `third-party/sysdeps/common/sqlite3/stage/lib/cmake/sqlite3/`  
**Config Template**: `third-party/sysdeps/common/sqlite3/sqlite3-config.cmake.in`

#### 45. numactl

**Config Path**: `third-party/sysdeps/linux/numactl/stage/lib/cmake/numa/`  
**Config Template**: `third-party/sysdeps/linux/numactl/numa-config.cmake.in`

#### 46. elfutils (libelf, libdw)

**Config Paths**:
- `third-party/sysdeps/linux/elfutils/stage/lib/cmake/libelf/`
- `third-party/sysdeps/linux/elfutils/stage/lib/cmake/libdw/`

**Config Templates**:
- `third-party/sysdeps/linux/elfutils/libelf-config.cmake.in`
- `third-party/sysdeps/linux/elfutils/libdw-config.cmake.in`

---

## Build-Time Path Resolution

### How CMake Finds Packages in TheRock

1. **Dependency Provider**: TheRock uses a custom dependency provider
   - File: Generated dynamically per subproject
   - Located in: `<subproject>/build/dep_provider.cmake`
   - Registers all provided packages from dependencies

2. **CMAKE_PREFIX_PATH**: Automatically set to include:
   - All RUNTIME_DEPS stage directories
   - All BUILD_DEPS stage directories
   - Transitive dependencies

3. **find_package()** Resolution Order:
   ```cmake
   find_package(<package>)
   ```
   - First checks: `CMAKE_PREFIX_PATH`
   - Looks in: `<prefix>/lib/cmake/<package>/`
   - Finds: `<package>-config.cmake`

### Example: hipBLAS Finding rocBLAS

When hipBLAS is configured:

1. **Dependency Declaration**:
   ```cmake
   RUNTIME_DEPS rocBLAS
   ```

2. **Generated CMAKE_PREFIX_PATH**:
   ```cmake
   set(CMAKE_PREFIX_PATH 
     "${THEROCK_BINARY_DIR}/math-libs/BLAS/rocBLAS/stage"
     ...
   )
   ```

3. **find_package() Call** (in hipBLAS/CMakeLists.txt):
   ```cmake
   find_package(rocblas REQUIRED)
   ```

4. **Resolution**:
   - Searches: `math-libs/BLAS/rocBLAS/stage/lib/cmake/rocblas/`
   - Finds: `rocblas-config.cmake`
   - Imports: `rocblas::rocblas` target

---

## CMake Package Discovery

### Package Advertising

Subprojects advertise CMake packages using:

```cmake
therock_cmake_subproject_provide_package(<subproject> <package> <relative_path>)
```

**Parameters**:
- `<subproject>`: Subproject target name
- `<package>`: CMake package name (for `find_package()`)
- `<relative_path>`: Path relative to stage directory

**Examples**:

```cmake
# rocBLAS provides "rocblas" package at lib/cmake/rocblas
therock_cmake_subproject_provide_package(rocBLAS rocblas lib/cmake/rocblas)

# LLVM provides multiple packages at lib/llvm/lib/cmake/...
therock_cmake_subproject_provide_package(amd-llvm LLVM lib/llvm/lib/cmake/llvm)
therock_cmake_subproject_provide_package(amd-llvm Clang lib/llvm/lib/cmake/clang)
```

### Package Resolution in Dependencies

When a subproject depends on another:

```cmake
therock_cmake_subproject_declare(hipblas
  RUNTIME_DEPS
    rocBLAS
)
```

TheRock automatically:
1. Adds rocBLAS's stage directory to CMAKE_PREFIX_PATH
2. Includes all CMake packages provided by rocBLAS
3. Makes `rocblas` package available to `find_package(rocblas)`

---

## Quick Reference Tables

### Top-Level Component Directories

| Component       | Location           | Contains                       |
| --------------- | ------------------ | ------------------------------ |
| Base            | `base/`            | rocm-core, rocm-cmake, smi     |
| Compiler        | `compiler/`        | LLVM, comgr, hipcc, hipify     |
| Core            | `core/`            | HSA runtime, HIP, OpenCL       |
| Math-libs       | `math-libs/`       | BLAS, RAND, FFT, PRIM, SOLVER  |
| ML-libs         | `ml-libs/`         | MIOpen, CK, hipDNN             |
| Comm-libs       | `comm-libs/`       | RCCL                           |
| Profiler        | `profiler/`        | rocprofiler, roctracer         |
| Third-party     | `third-party/`     | Bundled dependencies           |

### CMake Config Naming Patterns

| Pattern                          | Example                                     |
| -------------------------------- | ------------------------------------------- |
| `<package>-config.cmake`         | `rocblas-config.cmake`                      |
| `<package>-config-version.cmake` | `rocblas-config-version.cmake`              |
| `<package>-targets.cmake`        | `rocblas-targets.cmake`                     |
| `<package>-targets-*.cmake`      | `rocblas-targets-release.cmake`             |
| `<Package>Config.cmake`          | `LLVMConfig.cmake` (LLVM uses this format)  |
| `<Package>ConfigVersion.cmake`   | `LLVMConfigVersion.cmake`                   |

### Build Commands

```bash
# Configure specific subproject
cmake -B build -GNinja -DTHEROCK_AMDGPU_FAMILIES=gfx110X-dgpu

# Build specific subproject
cmake --build build --target rocblas

# Build + stage install
cmake --build build --target rocblas+stage

# View installed CMake configs
ls build/math-libs/BLAS/rocBLAS/stage/lib/cmake/rocblas/

# Build all artifacts
cmake --build build --target therock-artifacts

# Build specific artifact
cmake --build build --target artifact-blas
```

---

## Summary Statistics

- **Total Subprojects with CMake Configs**: ~45+
- **Base/Infrastructure Packages**: 6
- **Compiler Packages**: 10 (LLVM provides 4, comgr, hipcc, etc.)
- **Runtime Packages**: 5 (HSA, HIP, OpenCL)
- **Math Library Packages**: 15+ (BLAS, FFT, RAND, PRIM, SOLVER families)
- **ML Library Packages**: 4 (MIOpen, CK, hipDNN, plugin)
- **Communication Packages**: 1 (RCCL)
- **Profiler Packages**: 3 (rocprofiler-sdk, roctracer, aqlprofile)
- **Third-Party Packages**: 8+ (bundled system dependencies)

---

## Notes

1. **LLVM Special Case**: LLVM installs to `lib/llvm/` subdirectory with configs at `lib/llvm/lib/cmake/`. Overlay configs in `base/aux-overlay` provide top-level access.

2. **Delay-Load COMGR**: When `THEROCK_FLAG_COMGR_DELAY_LOAD=ON`, the amd-comgr-stub provides the `amd_comgr` package instead of amd-comgr directly.

3. **Package Name Aliases**: Some packages (like HIP) provide multiple names:
   - `hip` and `HIP` both resolve to the same config
   - Both are advertised for compatibility

4. **Stage Directory Reuse**: Multiple artifacts can source from the same stage directory, selecting different component subdirectories.

5. **Prebuilt Markers**: If `<subproject>/stage.prebuilt` exists, the subproject won't be rebuilt and the existing stage directory is used.

6. **GPU-Specific Builds**: Math and ML libraries are built per-GPU-family. The stage directory name doesn't change, but separate builds occur for each target family specified in `THEROCK_AMDGPU_FAMILIES`.

---

## References

- TheRock Repository: https://github.com/ROCm/TheRock
- Subproject System: `cmake/therock_subproject.cmake`
- Artifacts System: `cmake/therock_artifacts.cmake`
- Build Documentation: `docs/development/build_system.md`


