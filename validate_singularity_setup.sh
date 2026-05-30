#!/usr/bin/env bash
#
# Validate that the Lizard Wizard Singularity/Apptainer images exist and run.
#
# Checks that all four .sif files are present in the container directory and
# that each one can execute a trivial command (`python --version`). This catches
# the most common failure modes: a build that silently produced no image, or an
# image whose conda env did not get created.
#
# Usage:
#   ./validate_singularity_setup.sh                 # check ./singularity
#   ./validate_singularity_setup.sh /path/to/dir    # check a custom dir
#   LZW_SINGULARITY_PATH=/path ./validate_singularity_setup.sh
#
# Exit code is non-zero if any container is missing or fails to run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve the container directory: CLI arg > LZW_SINGULARITY_PATH > ./singularity
CONTAINER_DIR="${1:-${LZW_SINGULARITY_PATH:-${SCRIPT_DIR}/singularity}}"

if command -v apptainer >/dev/null 2>&1; then
  RUNNER="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  RUNNER="singularity"
else
  echo "ERROR: neither 'apptainer' nor 'singularity' found on PATH." >&2
  exit 1
fi

echo "Runner:        ${RUNNER}"
echo "Container dir: ${CONTAINER_DIR}"
echo

CONTAINERS=(caiman cellpose summary wizards_staff)
status=0

for name in "${CONTAINERS[@]}"; do
  sif="${CONTAINER_DIR}/${name}.sif"
  if [[ ! -f "${sif}" ]]; then
    echo "MISSING  ${name}.sif  (build it with ./build_singularity_containers.sh)"
    status=1
    continue
  fi
  if ${RUNNER} exec "${sif}" python --version >/dev/null 2>&1; then
    echo "OK       ${name}.sif"
  else
    echo "FAILED   ${name}.sif  (image present but 'python --version' did not run)"
    status=1
  fi
done

echo
if [[ "${status}" -eq 0 ]]; then
  echo "All containers present and runnable."
else
  echo "One or more containers are missing or broken; see above." >&2
fi
exit "${status}"
