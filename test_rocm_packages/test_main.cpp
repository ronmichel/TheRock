/**
 * ROCm Package Configuration Test Application
 * 
 * This application tests that ROCm packages can be found, linked,
 * and basic functionality works at runtime.
 */

#include <iostream>
#include <string>
#include <vector>

// Conditional includes based on what was found
#ifdef __has_include
  #if __has_include(<hip/hip_runtime.h>)
    #define HAS_HIP
    #include <hip/hip_runtime.h>
  #endif
  
  #if __has_include(<hsa/hsa.h>)
    #define HAS_HSA
    #include <hsa/hsa.h>
  #endif
  
  #if __has_include(<rocblas/rocblas.h>)
    #define HAS_ROCBLAS
    #include <rocblas/rocblas.h>
  #endif
  
  #if __has_include(<hipblas/hipblas.h>)
    #define HAS_HIPBLAS
    #include <hipblas/hipblas.h>
  #endif
  
  #if __has_include(<rocfft/rocfft.h>)
    #define HAS_ROCFFT
    #include <rocfft/rocfft.h>
  #endif
  
  #if __has_include(<rocrand/rocrand.h>)
    #define HAS_ROCRAND
    #include <rocrand/rocrand.h>
  #endif
  
  #if __has_include(<rocsparse/rocsparse.h>)
    #define HAS_ROCSPARSE
    #include <rocsparse/rocsparse.h>
  #endif
  
  #if __has_include(<rocsolver/rocsolver.h>)
    #define HAS_ROCSOLVER
    #include <rocsolver/rocsolver.h>
  #endif
#endif

class TestResults {
public:
    void addTest(const std::string& name, bool passed, const std::string& message = "") {
        tests_.push_back({name, passed, message});
        if (passed) passed_++; else failed_++;
    }
    
    void printSummary() const {
        std::cout << "\n";
        std::cout << "========================================\n";
        std::cout << "Test Summary\n";
        std::cout << "========================================\n";
        std::cout << "Total tests: " << tests_.size() << "\n";
        std::cout << "Passed: " << passed_ << "\n";
        std::cout << "Failed: " << failed_ << "\n";
        std::cout << "\n";
        
        for (const auto& test : tests_) {
            std::cout << (test.passed ? "✓ PASS" : "✗ FAIL") << ": " << test.name;
            if (!test.message.empty()) {
                std::cout << " - " << test.message;
            }
            std::cout << "\n";
        }
        std::cout << "========================================\n";
    }
    
    int getExitCode() const { return (failed_ > 0) ? 1 : 0; }
    
private:
    struct Test {
        std::string name;
        bool passed;
        std::string message;
    };
    std::vector<Test> tests_;
    int passed_ = 0;
    int failed_ = 0;
};

// Test HIP runtime
void testHIP(TestResults& results) {
#ifdef HAS_HIP
    int deviceCount = 0;
    hipError_t err = hipGetDeviceCount(&deviceCount);
    
    if (err == hipSuccess) {
        results.addTest("HIP: Get Device Count", true, 
                       "Found " + std::to_string(deviceCount) + " device(s)");
        
        if (deviceCount > 0) {
            hipDeviceProp_t prop;
            err = hipGetDeviceProperties(&prop, 0);
            if (err == hipSuccess) {
                results.addTest("HIP: Get Device Properties", true, 
                               std::string("Device: ") + prop.name);
            } else {
                results.addTest("HIP: Get Device Properties", false, 
                               "hipGetDeviceProperties failed");
            }
        }
    } else {
        results.addTest("HIP: Get Device Count", false, 
                       "hipGetDeviceCount failed with error " + std::to_string(err));
    }
#else
    results.addTest("HIP", false, "Not compiled with HIP support");
#endif
}

// Test HSA runtime
void testHSA(TestResults& results) {
#ifdef HAS_HSA
    hsa_status_t status = hsa_init();
    if (status == HSA_STATUS_SUCCESS) {
        results.addTest("HSA: Initialize", true);
        hsa_shut_down();
    } else {
        results.addTest("HSA: Initialize", false, 
                       "hsa_init failed with status " + std::to_string(status));
    }
#else
    results.addTest("HSA", false, "Not compiled with HSA support");
#endif
}

// Test rocBLAS
void testROCBLAS(TestResults& results) {
#ifdef HAS_ROCBLAS
    rocblas_handle handle;
    rocblas_status status = rocblas_create_handle(&handle);
    
    if (status == rocblas_status_success) {
        results.addTest("rocBLAS: Create Handle", true);
        
        // Get version
        char version[256];
        rocblas_get_version_string(version, sizeof(version));
        results.addTest("rocBLAS: Get Version", true, 
                       std::string("Version: ") + version);
        
        rocblas_destroy_handle(handle);
    } else {
        results.addTest("rocBLAS: Create Handle", false, 
                       "rocblas_create_handle failed");
    }
#else
    results.addTest("rocBLAS", false, "Not compiled with rocBLAS support");
#endif
}

// Test hipBLAS
void testHIPBLAS(TestResults& results) {
#ifdef HAS_HIPBLAS
    hipblasHandle_t handle;
    hipblasStatus_t status = hipblasCreate(&handle);
    
    if (status == HIPBLAS_STATUS_SUCCESS) {
        results.addTest("hipBLAS: Create Handle", true);
        hipblasDestroy(handle);
    } else {
        results.addTest("hipBLAS: Create Handle", false, 
                       "hipblasCreate failed");
    }
#else
    results.addTest("hipBLAS", false, "Not compiled with hipBLAS support");
#endif
}

// Test rocFFT
void testROCFFT(TestResults& results) {
#ifdef HAS_ROCFFT
    char version[256];
    rocfft_get_version_string(version, sizeof(version));
    results.addTest("rocFFT: Get Version", true, 
                   std::string("Version: ") + version);
#else
    results.addTest("rocFFT", false, "Not compiled with rocFFT support");
#endif
}

// Test rocRAND
void testROCRAND(TestResults& results) {
#ifdef HAS_ROCRAND
    int version;
    rocrand_status status = rocrand_get_version(&version);
    
    if (status == ROCRAND_STATUS_SUCCESS) {
        results.addTest("rocRAND: Get Version", true, 
                       "Version: " + std::to_string(version));
    } else {
        results.addTest("rocRAND: Get Version", false, 
                       "rocrand_get_version failed");
    }
#else
    results.addTest("rocRAND", false, "Not compiled with rocRAND support");
#endif
}

// Test rocSPARSE
void testROCSPARSE(TestResults& results) {
#ifdef HAS_ROCSPARSE
    rocsparse_handle handle;
    rocsparse_status status = rocsparse_create_handle(&handle);
    
    if (status == rocsparse_status_success) {
        results.addTest("rocSPARSE: Create Handle", true);
        
        // Get version
        int version;
        rocsparse_get_version(handle, &version);
        results.addTest("rocSPARSE: Get Version", true, 
                       "Version: " + std::to_string(version));
        
        rocsparse_destroy_handle(handle);
    } else {
        results.addTest("rocSPARSE: Create Handle", false, 
                       "rocsparse_create_handle failed");
    }
#else
    results.addTest("rocSPARSE", false, "Not compiled with rocSPARSE support");
#endif
}

// Test rocSOLVER
void testROCSOLVER(TestResults& results) {
#ifdef HAS_ROCSOLVER
    rocblas_handle handle;
    rocblas_status status = rocblas_create_handle(&handle);
    
    if (status == rocblas_status_success) {
        // rocSOLVER uses rocBLAS handle
        results.addTest("rocSOLVER: Use rocBLAS Handle", true);
        
        char version[256];
        rocsolver_get_version_string(version, sizeof(version));
        results.addTest("rocSOLVER: Get Version", true, 
                       std::string("Version: ") + version);
        
        rocblas_destroy_handle(handle);
    } else {
        results.addTest("rocSOLVER: Use rocBLAS Handle", false);
    }
#else
    results.addTest("rocSOLVER", false, "Not compiled with rocSOLVER support");
#endif
}

int main(int argc, char** argv) {
    std::cout << "========================================\n";
    std::cout << "ROCm Package Runtime Test\n";
    std::cout << "========================================\n";
    std::cout << "\n";
    
    TestResults results;
    
    // Run all tests
    std::cout << "Running runtime tests...\n\n";
    
    testHIP(results);
    testHSA(results);
    testROCBLAS(results);
    testHIPBLAS(results);
    testROCFFT(results);
    testROCRAND(results);
    testROCSPARSE(results);
    testROCSOLVER(results);
    
    // Print summary
    results.printSummary();
    
    return results.getExitCode();
}


