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

### Package Naming

### Device-Specific Architecture Packages

## Python Packaging Requirements


This will reduce the number of packages visibile via the package manager.

### Meta Packages

