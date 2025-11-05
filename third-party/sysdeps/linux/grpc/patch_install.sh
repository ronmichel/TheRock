#!/bin/bash
set -e

PREFIX="${1:?Expected install prefix argument}"
PATCHELF="${PATCHELF:-patchelf}"
THEROCK_SOURCE_DIR="${THEROCK_SOURCE_DIR:?THEROCK_SOURCE_DIR not defined}"
Python3_EXECUTABLE="${Python3_EXECUTABLE:?Python3_EXECUTABLE not defined}"

# Patch all shared libraries in lib/ with rocm_sysdeps_ prefix
# This includes gRPC, protobuf, abseil, re2, cares, and ssl libraries
echo "Patching shared libraries in $PREFIX/lib"

# Find all .so files and patch them
find "$PREFIX/lib" -name "*.so*" -type f | while read -r sofile; do
  if file "$sofile" | grep -q "ELF.*shared object"; then
    echo "Processing: $sofile"
    "$Python3_EXECUTABLE" "$THEROCK_SOURCE_DIR/build_tools/patch_linux_so.py" \
      --patchelf "${PATCHELF}" --add-prefix rocm_sysdeps_ \
      "$sofile"
  fi
done

# Update .pc files to use relative paths
if [ -d "$PREFIX/lib/pkgconfig" ]; then
  echo "Updating pkgconfig files"
  for pcfile in "$PREFIX/lib/pkgconfig"/*.pc; do
    if [ -f "$pcfile" ]; then
      sed -i -E 's|^prefix=.+|prefix=${pcfiledir}/../..|' "$pcfile"
      sed -i -E 's|^exec_prefix=.+|exec_prefix=${prefix}|' "$pcfile"
      sed -i -E 's|^libdir=.+|libdir=${prefix}/lib|' "$pcfile"
      sed -i -E 's|^includedir=.+|includedir=${prefix}/include|' "$pcfile"
    fi
  done
fi

# Update CMake config files to be relocatable
echo "Updating CMake config files"

# Update gRPC CMake configs
if [ -d "$PREFIX/lib/cmake/grpc" ]; then
  for cmfile in "$PREFIX/lib/cmake/grpc"/*.cmake; do
    if [ -f "$cmfile" ]; then
      # Make paths relative by using CMAKE_CURRENT_LIST_DIR
      sed -i 's|INTERFACE_INCLUDE_DIRECTORIES "[^"]*include|INTERFACE_INCLUDE_DIRECTORIES "${_IMPORT_PREFIX}/include|g' "$cmfile"
      sed -i 's|IMPORTED_LOCATION "[^"]*lib/\([^"]*\)"|IMPORTED_LOCATION "${_IMPORT_PREFIX}/lib/\1"|g' "$cmfile"
    fi
  done
fi

# Update protobuf CMake configs
if [ -d "$PREFIX/lib/cmake/protobuf" ]; then
  for cmfile in "$PREFIX/lib/cmake/protobuf"/*.cmake; do
    if [ -f "$cmfile" ]; then
      sed -i 's|INTERFACE_INCLUDE_DIRECTORIES "[^"]*include|INTERFACE_INCLUDE_DIRECTORIES "${_IMPORT_PREFIX}/include|g' "$cmfile"
      sed -i 's|IMPORTED_LOCATION "[^"]*lib/\([^"]*\)"|IMPORTED_LOCATION "${_IMPORT_PREFIX}/lib/\1"|g' "$cmfile"
    fi
  done
fi

# Update absl CMake configs
if [ -d "$PREFIX/lib/cmake/absl" ]; then
  for cmfile in "$PREFIX/lib/cmake/absl"/*.cmake; do
    if [ -f "$cmfile" ]; then
      sed -i 's|INTERFACE_INCLUDE_DIRECTORIES "[^"]*include|INTERFACE_INCLUDE_DIRECTORIES "${_IMPORT_PREFIX}/include|g' "$cmfile"
      sed -i 's|IMPORTED_LOCATION "[^"]*lib/\([^"]*\)"|IMPORTED_LOCATION "${_IMPORT_PREFIX}/lib/\1"|g' "$cmfile"
    fi
  done
fi

echo "gRPC patching completed successfully"

