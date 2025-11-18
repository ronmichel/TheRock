---
author: Liam Berry (LiamfBerry), Saad Rahim (saadrahim)
created: 2025-11-14
modified: 2025-11-17
status: draft
---

# TheRock Software Packaging Requirements

## Overview

With the implementation of TheRock build system new software packaging requirements need to be introduced to reflect TheRock's strategy. This RFC defines the cross-platform packaging, installation, versioning, and distribution requirements for TheRock; including the ROCm Core SDK and related ROCm software components. The scope of these requirments will cover OS distrobution packaging, Windows packaging requirements, and python packaging.

Our goals are to:

1. **Standardize packaging behaviour acros Linux, Windows, and Python ecosystems**
2. **Ensure predicatble upgrade behaviour, side-by-side support, and compatibility with OS package managers**
3. **Comply with legal, licensing, and redistrobution rules**
4. **Support automated packaging workflows in TheRock with productized deliverables**

## Scope

### In Scope

- Packaging formats: rpm, deb, msi, winget manifests, pip wheels, WheelNext
- GPU-architecture-specific package variants
- Side-by-side installation of ROCm Core SDK
- Repository metadata, signing, and precedence
- Development vs runtime package separation
- ASAN, debug, and source packages
- Naming conventions (AMD-generated vs native distorbutions)
- Nightly, prerelease, patch, and stable release version semantics
- Integration with TheRock build system

### Out of Scope

- Driver packaging (GPU driver is explicitly excluded from installers)
- Internal CI/CD implementation details
- Legacy ROCm 5.x / 6.x packaging
- Non-Linux UNIX variants

## Linux Packaging Requirements

### Directory Layout

The ROCm Core SDK must be installed under:

```
/opt/rocm/core-X.Y
```

Where:

- `X.Y` = major + minor version
- Patch versions must be in-place within the existing `X.Y` folder
- Side-by-side installation is supported only for major.minor releases, not patches

A softlink must exist as a path to the latest rocm and to the latest rocm minor release for a major release:

```
/opt/rocm/core/ -> /opt/rocm/core-8.1
/opt/rocm/core-8 -> /opt/rocm/core-8.1
```

The softlinks allow for an independent directory structure for ROCm expansions which must be in the following formating:

```
/opt/rocm/hpc-25.12.0
/opt/rocm/hpc/ -> /opt/rocm/hpc-26.2.0
```

### RPATH and Relocatability

- All ROCm packages must be built and shiped with `$ORIGIN`-based RPATH
- RPMs must honor the `--prefix` argument for relocatable installs
- Separate relocatable/reloc-rpms are not required

### Repository Layout

Repositories will follow the following structure:

```
repo.amd.com/rocm/packages/<primary_os>/
```

The primary OS root folder will include the following distrobutions where the packages can be found:

| Primary OS | Secondary |
| :------------- |:-------------|
| debian12 |  |
| ubuntu2204 |  |
| ubuntu2404 |  |
| rhel8 | Centros 8 |
| rhel9 | Oracle 9, Rock 9, Alma 9 |
| rhel10 |  |
| sles15 |  |
| azl3 |  |

ASAN packages may be separated into:

```
repo.amd.com/rocm/packages-asan/
```

This will reduce the number of packages visible via the package manager.

### Meta Packages

Using `yum` ROCm Core SDK runtime components and ROCm Core SDK runtime + development components can be installed.

```
yum install rocm
yum install rocm-core
yum install rocm-core-<ver>
yum install rocm-core-devel
yum install rocm-core-devel-<ver>
```
The following table shows the meta packages that will be available:

| Name | Content | Descripion |
| :------------- | :------------- | :------------- |
| rocm & rocm-core | runtime & libraries, components, runtime compiler, amd-smi, rocminfo | Needed to run software built with ROCm Core |
| rocm-core-devel | rocm-core + compiler cmake, static library files, and headers | Needed to build software with ROCm Core |
| rocm-devel-tools | Profiler, debugger, and related tools | Independent set of tools to debug and profile any application built with ROCm |
| rocm-fortran |  | Fortran compiler and related components |
| rocm-opencl |  | Components needed to run OpenCL |
| rocm-openmp |  | Components needed to build OpenMP |
| rocm-core-sdk |  | Everything |

### Package Naming

The four possible naming strategies for packages were analyzed:

1. Prefix `amd-`
2. Prefix `amdi-`: Legally the safest option as no one can claim to AMD incorporated
3. Suffix `-amd`
4. Do nothing: Manage through versioning

Note that `amd-smi` isn't very applicable to the first three proposed naming strategies and would possibly have to be an exception to this standardization.

TheRock must adopt `amdi-<package>` for Linus distro-native package disambiguation unless Legal or Branding teams choose an alternative.
This avoids namespace sonflicts with distro-provided packages.

### Device-Specific Architecture Packages

Local GPUs must have an autodetection mechanism via the package manager. Possible options for device-specific architecture packages can be seen in the table as shown:

| Component | Meta package for all device packages |
| :------------- | :------------- |
| component-host | Host only package |
| component-$device | $device is the llvm gfx architecture each device package must have no conflict with other devices |

Example: 

```
yum install miopen-gfx906 miopen-gfx908
apt intall rocm-gfx906 rocm-gfx-908 # Host + two device architectures
apt install rocm # Every architecture
```

All device-specific packages must:

- Not conflict with each other
- Be independently installable
- Support meta-packages
- Allow autodetection of local GPUs

TheRock must provide a GPU detection interface for package managers.

## Package Granularity 

## Python Packaging Requirements
