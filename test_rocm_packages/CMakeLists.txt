# ROCm Package Configuration Test Suite
# Tests all CMake package configs from TheRock at build-time and install-time

cmake_minimum_required(VERSION 3.25)
project(ROCmPackageTest VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Option to control test verbosity
option(ROCM_TEST_VERBOSE "Enable verbose package finding" ON)
option(ROCM_TEST_STRICT "Fail on any missing package" OFF)
option(ROCM_TEST_BUILD_EXECUTABLE "Build test executable" ON)

# Track results
set(ROCM_PACKAGES_FOUND "" CACHE INTERNAL "")
set(ROCM_PACKAGES_NOT_FOUND "" CACHE INTERNAL "")

# Macro to test finding a package
macro(test_find_package PKG_NAME)
  set(_components ${ARGN})
  
  if(ROCM_TEST_VERBOSE)
    message(STATUS "Testing: find_package(${PKG_NAME} ${_components})")
  endif()
  
  set(_required_flag)
  if(ROCM_TEST_STRICT)
    set(_required_flag REQUIRED)
  endif()
  
  if(_components)
    find_package(${PKG_NAME} ${_required_flag} QUIET COMPONENTS ${_components})
  else()
    find_package(${PKG_NAME} ${_required_flag} QUIET)
  endif()
  
  if(${PKG_NAME}_FOUND OR ${PKG_NAME}_FOUND)
    message(STATUS "✓ FOUND: ${PKG_NAME}")
    if(DEFINED ${PKG_NAME}_VERSION)
      message(STATUS "  Version: ${${PKG_NAME}_VERSION}")
    endif()
    if(DEFINED ${PKG_NAME}_DIR)
      message(STATUS "  Config: ${${PKG_NAME}_DIR}")
    endif()
    list(APPEND ROCM_PACKAGES_FOUND ${PKG_NAME})
    set(ROCM_PACKAGE_${PKG_NAME}_FOUND TRUE)
  else()
    message(STATUS "✗ NOT FOUND: ${PKG_NAME}")
    list(APPEND ROCM_PACKAGES_NOT_FOUND ${PKG_NAME})
    set(ROCM_PACKAGE_${PKG_NAME}_FOUND FALSE)
  endif()
endmacro()

message(STATUS "=============================================================")
message(STATUS "ROCm Package Configuration Test")
message(STATUS "=============================================================")
message(STATUS "CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH}")
message(STATUS "Testing build: ${PROJECT_BINARY_DIR}")
message(STATUS "=============================================================")

# ============================================================================
# BASE PACKAGES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Base Packages ---")

test_find_package(rocm-core)
test_find_package(ROCmCMakeBuildTools)
test_find_package(ROCM)
test_find_package(half)
test_find_package(rocm_smi)
test_find_package(amd_smi)
test_find_package(rocprofiler-register)

# ============================================================================
# COMPILER PACKAGES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Compiler Packages ---")

test_find_package(LLVM)
test_find_package(Clang)
test_find_package(LLD)
test_find_package(AMDDeviceLibs)
test_find_package(amd_comgr)
test_find_package(hipcc)

# ============================================================================
# RUNTIME PACKAGES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Runtime Packages ---")

test_find_package(hsa-runtime64)
test_find_package(hsakmt)
test_find_package(hip)
test_find_package(HIP)  # Alias
test_find_package(hip-lang)
test_find_package(hiprtc)
test_find_package(ocl-icd)

# ============================================================================
# PROFILER PACKAGES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Profiler Packages ---")

test_find_package(rocprofiler-sdk)
test_find_package(roctracer)
test_find_package(hsa-amd-aqlprofile)

# ============================================================================
# MATH LIBRARIES - PRIM
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing PRIM Packages ---")

test_find_package(rocprim)
test_find_package(hipcub)
test_find_package(rocthrust)

# ============================================================================
# MATH LIBRARIES - RAND
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing RAND Packages ---")

test_find_package(rocrand)
test_find_package(hiprand)

# ============================================================================
# MATH LIBRARIES - FFT
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing FFT Packages ---")

test_find_package(rocfft)
test_find_package(hipfft)

# ============================================================================
# MATH LIBRARIES - BLAS
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing BLAS Packages ---")

test_find_package(rocblas)
test_find_package(hipblas)
test_find_package(hipblaslt)
test_find_package(hipblas-common)

# ============================================================================
# MATH LIBRARIES - SPARSE
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing SPARSE Packages ---")

test_find_package(rocsparse)
test_find_package(hipsparse)
test_find_package(hipsparselt)

# ============================================================================
# MATH LIBRARIES - SOLVER
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing SOLVER Packages ---")

test_find_package(rocsolver)
test_find_package(hipsolver)

# ============================================================================
# ML LIBRARIES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing ML Packages ---")

test_find_package(miopen)
test_find_package(composable_kernel)
test_find_package(hipdnn)

# ============================================================================
# COMMUNICATION LIBRARIES
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Communication Packages ---")

test_find_package(rccl)

# ============================================================================
# THIRD-PARTY PACKAGES (Bundled Dependencies)
# ============================================================================
message(STATUS "")
message(STATUS "--- Testing Third-Party Packages ---")

test_find_package(ZLIB)
test_find_package(zstd)
test_find_package(BZip2)
test_find_package(LibLZMA)
test_find_package(SQLite3)

# Linux-specific
if(UNIX AND NOT APPLE)
  test_find_package(numa)
  test_find_package(libelf)
  test_find_package(libdw)
endif()

# ============================================================================
# SUMMARY
# ============================================================================
message(STATUS "")
message(STATUS "=============================================================")
message(STATUS "Test Summary")
message(STATUS "=============================================================")

list(LENGTH ROCM_PACKAGES_FOUND _found_count)
list(LENGTH ROCM_PACKAGES_NOT_FOUND _not_found_count)
math(EXPR _total_count "${_found_count} + ${_not_found_count}")

message(STATUS "Total packages tested: ${_total_count}")
message(STATUS "Packages found: ${_found_count}")
message(STATUS "Packages not found: ${_not_found_count}")

if(_not_found_count GREATER 0)
  message(STATUS "")
  message(STATUS "Packages NOT found:")
  foreach(_pkg ${ROCM_PACKAGES_NOT_FOUND})
    message(STATUS "  - ${_pkg}")
  endforeach()
endif()

message(STATUS "=============================================================")

# ============================================================================
# BUILD TEST EXECUTABLE
# ============================================================================
if(ROCM_TEST_BUILD_EXECUTABLE)
  message(STATUS "")
  message(STATUS "--- Building Test Executable ---")
  
  # Only build executable if we have minimum required packages
  if(ROCM_PACKAGE_hip_FOUND)
    add_executable(rocm_package_test
      test_main.cpp
    )
    
    target_compile_features(rocm_package_test PRIVATE cxx_std_17)
    
    # Link against found packages
    set(_link_libs)
    
    if(ROCM_PACKAGE_hip_FOUND)
      target_link_libraries(rocm_package_test PRIVATE hip::host)
      list(APPEND _link_libs "hip::host")
    endif()
    
    if(ROCM_PACKAGE_rocblas_FOUND)
      target_link_libraries(rocm_package_test PRIVATE roc::rocblas)
      list(APPEND _link_libs "roc::rocblas")
    endif()
    
    if(ROCM_PACKAGE_hipblas_FOUND)
      target_link_libraries(rocm_package_test PRIVATE roc::hipblas)
      list(APPEND _link_libs "roc::hipblas")
    endif()
    
    if(ROCM_PACKAGE_rocfft_FOUND)
      target_link_libraries(rocm_package_test PRIVATE roc::rocfft)
      list(APPEND _link_libs "roc::rocfft")
    endif()
    
    if(ROCM_PACKAGE_rocrand_FOUND)
      target_link_libraries(rocm_package_test PRIVATE roc::rocrand)
      list(APPEND _link_libs "roc::rocrand")
    endif()
    
    if(ROCM_PACKAGE_hsa-runtime64_FOUND)
      target_link_libraries(rocm_package_test PRIVATE hsa-runtime64::hsa-runtime64)
      list(APPEND _link_libs "hsa-runtime64::hsa-runtime64")
    endif()
    
    message(STATUS "Test executable will link: ${_link_libs}")
    
    # Install
    install(TARGETS rocm_package_test
      RUNTIME DESTINATION bin
    )
    
    # Add test
    enable_testing()
    add_test(NAME rocm_package_runtime_test
      COMMAND rocm_package_test
    )
    
  else()
    message(STATUS "Skipping test executable (HIP not found)")
  endif()
endif()

# ============================================================================
# GENERATE REPORT
# ============================================================================
configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/test_report.txt.in
  ${CMAKE_CURRENT_BINARY_DIR}/test_report.txt
  @ONLY
)

message(STATUS "")
message(STATUS "Test report generated: ${CMAKE_CURRENT_BINARY_DIR}/test_report.txt")
message(STATUS "")


