################################################################################
# ROCm Systems Tools
################################################################################

if(THEROCK_ENABLE_RDC)
    ##########
    # RDC (ROCm Data Center Tool)
    ##########

    # Point GRPC_ROOT to the actual gRPC build location
    # RDC's CMakeLists.txt will try to install gRPC from this location,
    # and TheRock will also merge it via RUNTIME_DEPS
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
            # Pass gRPC installation directory - point to actual gRPC build location
            # RDC will install gRPC files, and TheRock will also merge them (duplicates are ok)
            "-DGRPC_ROOT=${_grpc_build_path}"
            -DGRPC_DESIRED_VERSION=1.76.0
            # Add gRPC bin directory to program search path for protoc and grpc_cpp_plugin
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
                    "${CMAKE_CURRENT_BINARY_DIR}/dist/lib/rdc/${lib_name}"
        )
    endforeach()

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
