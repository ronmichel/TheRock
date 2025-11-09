if(THEROCK_ENABLE_ROCPROFV3)
  set(_rocprofiler_sdk_optional_deps)

  ##############################################################################
  # rocprof-trace-decoder-binary
  # The trace decoder is responsible for decoding advanced thread traces from
  # the GPU. It is a binary-only dependency of ROCm which is enabled at
  # runtime via `rocprofv3 --att`. If an appropriate shared library is adjacent
  # to the profiler shared libraries, it will be used by default.
  # See: https://github.com/ROCm/rocprof-trace-decoder/
  # The binaries are contained in the submodule rocprof-trace-decoder/binaries
  # Our CMakeLists which installs them is local to this project.
  ##############################################################################
  if(THEROCK_ENABLE_ROCPROF_TRACE_DECODER_BINARY)
    therock_cmake_subproject_declare(rocprof-trace-decoder
      EXTERNAL_SOURCE_DIR "rocprof-trace-decoder"
      BACKGROUND_BUILD
    )
    therock_cmake_subproject_activate(rocprof-trace-decoder)
    list(APPEND _rocprofiler_sdk_optional_deps rocprof-trace-decoder)
  endif()

  ##############################################################################
  # aqlprofile
  ##############################################################################
  therock_cmake_subproject_declare(aqlprofile
    # TODO: Tests do not build properly for explicit targets: Switch to
    # USE_DIST_AMDGPU_TARGETS once fixed.
    # See: https://github.com/ROCm/aqlprofile/issues/2
    DISABLE_AMDGPU_TARGETS
    EXTERNAL_SOURCE_DIR "${THEROCK_ROCM_SYSTEMS_SOURCE_DIR}/projects/aqlprofile"
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/aqlprofile"
    BACKGROUND_BUILD
    INTERFACE_LINK_DIRS
      lib  # So that dependents can find the aqlprofile library via find_library
    RUNTIME_DEPS
      amd-llvm
      ROCR-Runtime
  )
  therock_cmake_subproject_glob_c_sources(aqlprofile
    SUBDIRS .
  )
  therock_cmake_subproject_activate(aqlprofile)

  ##############################################################################
  # rocprofiler-sdk
  ##############################################################################
  # Detect available Default Python3 version on the system or
  # use explicitly provided Python3 versions
  therock_detect_python_versions(_detected_python_executables _detected_python_versions)

  # Use detected versions or fall back to default if none found
  if(NOT _detected_python_versions)
    message(FATAL_ERROR "No Python versions detected for rocprofiler-sdk")
    set(_detected_python_versions_str "")
  else()
    message(STATUS "Detected Python versions for rocprofiler-sdk python bindings: ${_detected_python_versions}")
    message(STATUS "Python executables: ${_detected_python_executables}")
    # Join all detected Python versions into a single string separated by semicolons.
    # This is a workaround because therock_cmake_subproject_declare does not support passing lists directly.
    list(JOIN _detected_python_versions "\;" _detected_python_versions_str)
  endif()

  therock_cmake_subproject_declare(rocprofiler-sdk
    USE_DIST_AMDGPU_TARGETS
    EXTERNAL_SOURCE_DIR "${THEROCK_ROCM_SYSTEMS_SOURCE_DIR}/projects/rocprofiler-sdk"
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/rocprofiler-sdk"
    BACKGROUND_BUILD
    CMAKE_ARGS
      -DHIP_PLATFORM=amd
      -DROCPROFILER_PYTHON_VERSIONS:STRING="${_detected_python_versions_str}"
    CMAKE_INCLUDES
      therock_explicit_finders.cmake
    RUNTIME_DEPS
      aqlprofile
      hip-clr
      rocprofiler-register
      ${_rocprofiler_sdk_optional_deps}
      ${THEROCK_BUNDLED_ELFUTILS}
      ${THEROCK_BUNDLED_LIBDRM}
      ${THEROCK_BUNDLED_SQLITE3}
  )
  therock_cmake_subproject_glob_c_sources(rocprofiler-sdk
    SUBDIRS .
  )
  therock_cmake_subproject_provide_package(rocprofiler-sdk rocprofiler-sdk lib/cmake/rocprofiler-sdk)
  therock_cmake_subproject_provide_package(rocprofiler-sdk rocprofiler-sdk-roctx lib/cmake/rocprofiler-sdk-roctx)
  therock_cmake_subproject_activate(rocprofiler-sdk)

  ##############################################################################
  # roctracer
  # This is a very old, deprecated library with a number of quirks. Long term,
  # everything is supposed to migrate to rocprofiler-sdk, which has runtime
  # support to intercept any old roctracer clients when tracing is active.
  # To prepare for removal, anything that depends on roctracer should also
  # depend on rocprofiler-sdk.
  ##############################################################################

  therock_cmake_subproject_declare(roctracer
    USE_DIST_AMDGPU_TARGETS
    EXTERNAL_SOURCE_DIR "${THEROCK_ROCM_SYSTEMS_SOURCE_DIR}/projects/roctracer"
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/roctracer"
    BACKGROUND_BUILD
    COMPILER_TOOLCHAIN
      # Must build with the HIP compiler.
      amd-hip
    CMAKE_ARGS
      -DHIP_PLATFORM=amd
    INTERFACE_INCLUDE_DIRS
      # All old clients of roctx64 expect to just be able to find its include
      # with no further qualification. Bad design, but also deprecated, so meh.
      include
    INTERFACE_LINK_DIRS
      # So that dependents can find the roctx library via find_library()
      lib
    RUNTIME_DEPS
      hip-clr
      ROCR-Runtime
  )
  therock_cmake_subproject_glob_c_sources(roctracer
    SUBDIRS .
  )
  therock_cmake_subproject_activate(roctracer)

  ##############################################################################
  # RDC (ROCm Data Center Tool)
  # Data center management and monitoring tool that provides profiling and
  # telemetry capabilities through rocprofiler-sdk.
  ##############################################################################

  if(THEROCK_ENABLE_RDC)
    # Note: RUNTIME_DEPS includes ${THEROCK_BUNDLED_GRPC} which ensures:
    # 1. gRPC is built before RDC
    # 2. CMAKE_PREFIX_PATH includes gRPC's stage directory
    # 3. find_package(gRPC) and find_package(protobuf) will find the config files
    #
    # CMAKE_PROGRAM_PATH is kept temporarily to help find protoc and grpc_cpp_plugin
    # TODO: Test if this can be removed once gRPCConfig.cmake is verified to export tool paths correctly
    set(_grpc_build_path "${THEROCK_BINARY_DIR}/third-party/sysdeps/linux/grpc/build/stage/lib/rocm_sysdeps")

    therock_cmake_subproject_declare(rdc
      EXTERNAL_SOURCE_DIR "${THEROCK_ROCM_SYSTEMS_SOURCE_DIR}/projects/rdc"
      BACKGROUND_BUILD

      CMAKE_ARGS
        -DBUILD_PROFILER=ON
        # Enable rdcd and rdci with standalone mode
        -DBUILD_STANDALONE=ON
        -DBUILD_RUNTIME=ON
        -DBUILD_RVS=OFF
        -DBUILD_TESTS=ON
        -DHIP_PLATFORM=amd
        -DCMAKE_CXX_STANDARD=17
        # Help CMake find protoc and grpc_cpp_plugin executables
        # These are build-time tools needed to generate code from .proto files
        "-DCMAKE_PROGRAM_PATH=${_grpc_build_path}/bin"

      BUILD_DEPS
        amd-llvm

      RUNTIME_DEPS
        ROCR-Runtime
        amdsmi
        rocprofiler-sdk
        ${THEROCK_BUNDLED_LIBCAP}
        ${THEROCK_BUNDLED_ZLIB}
        ${THEROCK_BUNDLED_GRPC}

      INTERFACE_LINK_DIRS
        lib
    )

    therock_cmake_subproject_glob_c_sources(rdc
      SUBDIRS .
    )

    therock_cmake_subproject_provide_package(rdc rdc lib/cmake/rdc)

    therock_cmake_subproject_activate(rdc)

    # RDC: use custom bash script to validate shared libraries
    foreach(lib_name librdc_rocr.so librdc_rocp.so)
      add_test(
        NAME therock-validate-shared-lib-${lib_name}
        COMMAND
          "${CMAKE_CURRENT_SOURCE_DIR}/validate_rdc_library.sh"
            "${CMAKE_CURRENT_BINARY_DIR}/rdc/dist/lib/rdc/${lib_name}"
      )
    endforeach()

    # Provide RDC artifact
    therock_provide_artifact(rdc
      TARGET_NEUTRAL
      DESCRIPTOR artifact-rdc.toml
      COMPONENTS
        dbg
        dev
        doc
        lib
        run
      SUBPROJECT_DEPS
        amdsmi
        rocprofiler-sdk
        rdc
    )

  endif()

  therock_provide_artifact(rocprofiler-sdk
    TARGET_NEUTRAL
    DESCRIPTOR artifact-rocprofiler-sdk.toml
    COMPONENTS
      dbg
      dev
      doc
      lib
      run
    SUBPROJECT_DEPS
      aqlprofile
      rocprofiler-sdk
      roctracer
      ${_rocprofiler_sdk_optional_deps}
  )

endif(THEROCK_ENABLE_ROCPROFV3)
