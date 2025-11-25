#!/bin/bash
# ROCm Package Configuration Test Runner
# 
# Usage:
#   ./run_tests.sh [build|install] [rocm_path]
#
# Examples:
#   ./run_tests.sh build ../build/dist/rocm
#   ./run_tests.sh install /opt/rocm

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_TYPE="${1:-build}"
ROCM_PATH="${2:-../build/dist/rocm}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "ROCm Package Configuration Test Runner"
echo "========================================"
echo ""
echo "Test Type: $TEST_TYPE"
echo "ROCm Path: $ROCM_PATH"
echo ""

# Validate ROCm path
if [ ! -d "$ROCM_PATH" ]; then
    echo -e "${RED}Error: ROCm path not found: $ROCM_PATH${NC}"
    exit 1
fi

# Clean previous build
BUILD_DIR="$SCRIPT_DIR/build-${TEST_TYPE}"
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo ""
echo "========================================"
echo "Configuring CMake..."
echo "========================================"
echo ""

cmake .. \
    -DCMAKE_PREFIX_PATH="$ROCM_PATH" \
    -DROCM_TEST_VERBOSE=ON \
    -DROCM_TEST_BUILD_EXECUTABLE=ON \
    -DCMAKE_BUILD_TYPE=Release

echo ""
echo "========================================"
echo "Building..."
echo "========================================"
echo ""

cmake --build . -j$(nproc)

echo ""
echo "========================================"
echo "Test Results"
echo "========================================"
echo ""

# Check build status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Configuration and build succeeded${NC}"
else
    echo -e "${RED}✗ Configuration or build failed${NC}"
    exit 1
fi

# Display test report
if [ -f "test_report.txt" ]; then
    echo ""
    echo "--- Test Report ---"
    cat test_report.txt
fi

# Run executable test if it exists
if [ -f "./rocm_package_test" ]; then
    echo ""
    echo "========================================"
    echo "Running Runtime Tests..."
    echo "========================================"
    echo ""
    
    # Set library path for runtime
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        export LD_LIBRARY_PATH="$ROCM_PATH/lib:$LD_LIBRARY_PATH"
    fi
    
    ./rocm_package_test
    TEST_RESULT=$?
    
    echo ""
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ All runtime tests passed${NC}"
    else
        echo -e "${RED}✗ Some runtime tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Runtime test executable not built (HIP may not be available)${NC}"
fi

# Run CTest
echo ""
echo "========================================"
echo "Running CTest..."
echo "========================================"
echo ""

if command -v ctest &> /dev/null; then
    ctest --output-on-failure --verbose
    CTEST_RESULT=$?
    
    echo ""
    if [ $CTEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ All CTests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Some CTests failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ CTest not available${NC}"
fi

echo ""
echo "========================================"
echo "Test Complete"
echo "========================================"
echo ""
echo "Build directory: $BUILD_DIR"
echo "Test report: $BUILD_DIR/test_report.txt"
echo ""

exit 0


