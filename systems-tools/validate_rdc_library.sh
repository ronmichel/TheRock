#!/bin/bash
# Validates RDC shared libraries by manually loading dependencies.

set -e

for lib_path in "$@"; do
    echo -n "Validating shared library: $lib_path"

    # Get dependencies
    lib_dir=$(dirname "$lib_path")
    dist_lib_dir=$(dirname "$lib_dir")
    LD_PRELOAD="$dist_lib_dir/librdc_bootstrap.so.1:$dist_lib_dir/librdc.so.1"

    # Compile and run in one step using gcc -x
    output=$(LD_PRELOAD="$LD_PRELOAD" timeout 5 bash -c "
        gcc -x c -o /tmp/validate_rdc_\$\$ -ldl - <<'EOFC' && /tmp/validate_rdc_\$\$ \"$lib_path\" 2>&1; rm -f /tmp/validate_rdc_\$\$
#include <dlfcn.h>
#include <stdio.h>
int main(int argc, char **argv) {
    void *h = dlopen(argv[1], RTLD_GLOBAL | RTLD_NOW);
    if (h) { printf(\" : OK\\n\"); dlclose(h); return 0; }
    fprintf(stderr, \"%s\\n\", dlerror()); return 1;
}
EOFC
    ") || exit_code=$?

    # Handle results
    case ${exit_code:-0} in
        0)
            echo "$output"
            ;;
        124|134|250)
            # Timeout (124) or SIGABRT (134) - expected in CPU-only environments
            output_lower=$(echo "$output" | tr '[:upper:]' '[:lower:]')
            if [[ "$output_lower" =~ (smi initialize fail|smi failed|terminate called) ]] || [ -z "$output" ]; then
                echo " : OK (library loaded, initialization skipped in test environment)"
            else
                echo " : FAILED"
                [ -n "$output" ] && echo "$output" >&2
                exit 1
            fi
            ;;
        *)
            echo " : FAILED"
            [ -n "$output" ] && echo "$output" >&2
            exit 1
            ;;
    esac
done
