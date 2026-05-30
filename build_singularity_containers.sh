#!/usr/bin/env bash
#
# Build all Singularity/Apptainer containers for Lizard Wizard from the
# definition files in singularity/*.def.
#
# These containers are NOT published anywhere public: every user (including
# Arc-external users) builds them locally with this script. The resulting
# *.sif files are written to a directory of your choosing (default: ./singularity),
# which is also the default value of `params.singularity_path`.
#
# Requirements:
#   - Apptainer (>= 1.1) or Singularity (>= 3.8) on PATH
#   - Network egress (the .def files bootstrap from docker.io/mambaorg/micromamba
#     and pull conda/pip packages defined under envs/*.yml)
#   - ~10-20 GB free disk and ~15-40 min depending on network/CPU
#
# Usage:
#   ./build_singularity_containers.sh                 # build into ./singularity
#   ./build_singularity_containers.sh /path/to/out    # build into a custom dir
#   SUDO=1 ./build_singularity_containers.sh          # build with sudo (older Singularity)
#
# After building, run ./validate_singularity_setup.sh to confirm the images.

set -euo pipefail

# Directory holding this script (so it works from any CWD).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEF_DIR="${SCRIPT_DIR}/singularity"

# Output directory for the .sif files (defaults to ./singularity).
OUT_DIR="${1:-${SCRIPT_DIR}/singularity}"

# Pick a container builder: prefer apptainer, fall back to singularity.
if command -v apptainer >/dev/null 2>&1; then
  BUILDER="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  BUILDER="singularity"
else
  echo "ERROR: neither 'apptainer' nor 'singularity' found on PATH." >&2
  echo "Install Apptainer (https://apptainer.org/docs/admin/main/installation.html)" >&2
  echo "or Singularity, then re-run this script." >&2
  exit 1
fi

# Some sites require sudo for the build step; set SUDO=1 to enable.
SUDO_PREFIX=""
if [[ "${SUDO:-0}" == "1" ]]; then
  SUDO_PREFIX="sudo"
fi

echo "Builder:      ${BUILDER}"
echo "Def files in: ${DEF_DIR}"
echo "Output dir:   ${OUT_DIR}"
echo

mkdir -p "${OUT_DIR}"

# IMPORTANT: %files in the .def use paths relative to the build context, so we
# build from the repo root.
cd "${SCRIPT_DIR}"

CONTAINERS=(caiman cellpose summary wizards_staff)

for name in "${CONTAINERS[@]}"; do
  def="${DEF_DIR}/${name}.def"
  sif="${OUT_DIR}/${name}.sif"
  if [[ ! -f "${def}" ]]; then
    echo "ERROR: missing definition file ${def}" >&2
    exit 1
  fi
  echo ">>> Building ${name}.sif from ${name}.def ..."
  ${SUDO_PREFIX} ${BUILDER} build "${sif}" "${def}"
  echo ">>> Done: ${sif}"
  echo
done

echo "All containers built into: ${OUT_DIR}"
echo
echo "Point the pipeline at them with either:"
echo "  export LZW_SINGULARITY_PATH=${OUT_DIR}"
echo "or:"
echo "  nextflow run main.nf -profile singularity --singularity_path ${OUT_DIR} ..."
