#!/bin/bash
# Validates static library archives are well-formed and contain symbols.

set -e

for lib_path in "$@"; do
    echo -n "Validating static library: $lib_path"

    # Check if file exists
    if [ ! -f "$lib_path" ]; then
        echo " : FAILED"
        echo "  Error: File does not exist: $lib_path" >&2
        exit 1
    fi

    # Check if it's a valid archive using 'ar'
    if ! ar t "$lib_path" > /tmp/ar_output_$$ 2>&1; then
        echo " : FAILED"
        echo "  Error: Invalid archive format: $lib_path" >&2
        cat /tmp/ar_output_$$ >&2
        rm -f /tmp/ar_output_$$
        exit 1
    fi

    # Count object files
    object_count=$(wc -l < /tmp/ar_output_$$)
    rm -f /tmp/ar_output_$$

    if [ "$object_count" -eq 0 ]; then
        echo " : FAILED"
        echo "  Error: Archive is empty: $lib_path" >&2
        exit 1
    fi

    # Check that we can list symbols using 'nm'
    if ! nm --defined-only "$lib_path" > /tmp/nm_output_$$ 2>&1; then
        echo " : FAILED"
        echo "  Error: Cannot read symbols from archive: $lib_path" >&2
        cat /tmp/nm_output_$$ >&2
        rm -f /tmp/nm_output_$$
        exit 1
    fi

    # Count defined symbols (exclude undefined symbols marked with 'U')
    symbol_count=$(grep -v '^\s*U ' /tmp/nm_output_$$ | wc -l)
    rm -f /tmp/nm_output_$$

    if [ "$symbol_count" -eq 0 ]; then
        echo " : FAILED"
        echo "  Error: No defined symbols found: $lib_path" >&2
        exit 1
    fi

    echo " : OK ($object_count objects, $symbol_count symbols)"
done
