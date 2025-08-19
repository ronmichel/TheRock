# This finder resolves the virtual FFTW package for sub-projects.
# In reality the FFTW library installed in FFTW3 but we set also the
# FFTW_INCLUDE_DIRS and FFTW_LIBRARIES env variables without "3"
cmake_policy(PUSH)
cmake_policy(SET CMP0057 NEW)

message(STATUS "FindFFTW.cmake: Checking is FFTW in THEROCK_PROVIDED_PACKAGES")
if("FFTW3f" IN_LIST THEROCK_PROVIDED_PACKAGES)
  cmake_policy(POP)
  message(STATUS "FindFFTWf.cmake: Resolving FFTW3f single precision library version from the super-project")
  find_package(FFTW3f CONFIG REQUIRED)
else()
  cmake_policy(POP)
  set(FFTW3f_FOUND FALSE)
endif()
