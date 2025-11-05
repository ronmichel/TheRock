if(NOT CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  # When included in TheRock, we download sources and set up the sub-project.
  set(_source_dir "${CMAKE_CURRENT_BINARY_DIR}/source")
  set(_download_stamp "${_source_dir}/download.stamp")

  therock_subproject_fetch(therock-grpc-sources
    SOURCE_DIR "${_source_dir}"
    URL "https://github.com/grpc/grpc/archive/refs/tags/v1.76.0.tar.gz"
    URL_HASH "SHA256=9eb677e9b5889e1387399b69aedd9c9c68ff9f2ce2e21d60e2a7c08c8674aa98"
    TOUCH "${_download_stamp}"
  )

  therock_cmake_subproject_declare(therock-grpc
    EXTERNAL_SOURCE_DIR .
    BINARY_DIR build
    NO_MERGE_COMPILE_COMMANDS
    BACKGROUND_BUILD
    OUTPUT_ON_FAILURE
    CMAKE_ARGS
      "-DSOURCE_DIR=${_source_dir}"
      "-DPATCHELF=${PATCHELF}"
      "-DTHEROCK_SOURCE_DIR=${THEROCK_SOURCE_DIR}"
      "-DTHEROCK_BINARY_DIR=${THEROCK_BINARY_DIR}"
      "-DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
    RUNTIME_DEPS
      therock-zlib
    INSTALL_DESTINATION
      lib/rocm_sysdeps
    INTERFACE_INCLUDE_DIRS
      lib/rocm_sysdeps/include
    INTERFACE_LINK_DIRS
      lib/rocm_sysdeps/lib
    INTERFACE_INSTALL_RPATH_DIRS
      lib/rocm_sysdeps/lib
    INTERFACE_PKG_CONFIG_DIRS
      lib/rocm_sysdeps/lib/pkgconfig
    EXTRA_DEPENDS
      "${_download_stamp}"
  )
  therock_cmake_subproject_provide_package(therock-grpc gRPC lib/rocm_sysdeps/lib/cmake/grpc)
  therock_cmake_subproject_provide_package(therock-grpc protobuf lib/rocm_sysdeps/lib/cmake/protobuf)
  therock_cmake_subproject_activate(therock-grpc)

  therock_test_validate_shared_lib(
    PATH build/dist/lib/rocm_sysdeps/lib
    LIB_NAMES libgrpc++.so libgrpc.so libprotobuf.so
  )
  return()
endif()

# Otherwise, this is the sub-project build.
cmake_minimum_required(VERSION 3.25)
project(GRPC_BUILD)

include(ProcessorCount)
ProcessorCount(PAR_JOBS)

if(NOT PATCHELF)
  message(FATAL_ERROR "Missing PATCHELF from super-project")
endif()

# Set paths to find the already-built zlib
set(ZLIB_ROOT "${THEROCK_BINARY_DIR}/third-party/sysdeps/linux/zlib/build/stage/lib/rocm_sysdeps")
set(ZLIB_INCLUDE_DIR "${ZLIB_ROOT}/include")
set(ZLIB_LIBRARY "${ZLIB_ROOT}/lib/libz.so")

message(STATUS "Using zlib from: ${ZLIB_ROOT}")
message(STATUS "ZLIB_INCLUDE_DIR: ${ZLIB_INCLUDE_DIR}")
message(STATUS "ZLIB_LIBRARY: ${ZLIB_LIBRARY}")

add_custom_target(
  build ALL
  WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
  COMMAND
    "${CMAKE_COMMAND}" -E rm -rf -- "${CMAKE_INSTALL_PREFIX}" "${CMAKE_CURRENT_BINARY_DIR}/s" "${CMAKE_CURRENT_BINARY_DIR}/b"
  COMMAND
    "${CMAKE_COMMAND}" -E copy_directory "${SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/s"
  COMMAND
    "${CMAKE_COMMAND}"
      "-G${CMAKE_GENERATOR}"
      "-S${CMAKE_CURRENT_BINARY_DIR}/s"
      "-B${CMAKE_CURRENT_BINARY_DIR}/b"
      "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}"
      "-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}"
      "-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}"
      "-DCMAKE_CXX_STANDARD=17"
      "-DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}"
      "-DCMAKE_POSITION_INDEPENDENT_CODE=ON"
      # Use already-built zlib instead of rebuilding
      "-DgRPC_ZLIB_PROVIDER=package"
      "-DZLIB_ROOT=${ZLIB_ROOT}"
      "-DZLIB_INCLUDE_DIR=${ZLIB_INCLUDE_DIR}"
      "-DZLIB_LIBRARY=${ZLIB_LIBRARY}"
      # Build from submodules
      "-DgRPC_ABSL_PROVIDER=module"
      "-DgRPC_CARES_PROVIDER=module"
      "-DgRPC_RE2_PROVIDER=module"
      "-DgRPC_SSL_PROVIDER=module"
      "-DgRPC_PROTOBUF_PROVIDER=module"
      # Build options
      "-DgRPC_BUILD_TESTS=OFF"
      "-DgRPC_BUILD_CSHARP_EXT=OFF"
      "-DgRPC_BUILD_GRPC_CSHARP_PLUGIN=OFF"
      "-DgRPC_BUILD_GRPC_NODE_PLUGIN=OFF"
      "-DgRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN=OFF"
      "-DgRPC_BUILD_GRPC_PHP_PLUGIN=OFF"
      "-DgRPC_BUILD_GRPC_PYTHON_PLUGIN=OFF"
      "-DgRPC_BUILD_GRPC_RUBY_PLUGIN=OFF"
      "-DgRPC_INSTALL=ON"
      # Install to lib/ not lib64/
      "-DCMAKE_INSTALL_LIBDIR=lib"
      # Set RPATH for installed libraries
      "-DCMAKE_INSTALL_RPATH=\$ORIGIN"
      "-DCMAKE_BUILD_RPATH_USE_ORIGIN=ON"
  COMMAND
    "${CMAKE_COMMAND}" --build "${CMAKE_CURRENT_BINARY_DIR}/b" -j "${PAR_JOBS}"
  COMMAND
    "${CMAKE_COMMAND}" --install "${CMAKE_CURRENT_BINARY_DIR}/b"
  COMMAND
    "${CMAKE_COMMAND}" -E env
      "PATCHELF=${PATCHELF}"
      "THEROCK_SOURCE_DIR=${THEROCK_SOURCE_DIR}"
      "Python3_EXECUTABLE=${Python3_EXECUTABLE}" --
    bash "${CMAKE_CURRENT_SOURCE_DIR}/patch_install.sh" ${CMAKE_INSTALL_PREFIX}
  VERBATIM
)

