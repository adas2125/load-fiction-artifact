#!/usr/bin/env bash
set -euo pipefail

# Run from this directory, or call the script by path.
cd "$(dirname "$0")"

# setting host and port
HOST="${HOST:-localhost}"
PORT="${PORT:-8080}"
URL="${URL:-http://${HOST}:${PORT}/}"

# default LG settings
THREADS="${THREADS:-4}"
CONNECTIONS="${CONNECTIONS:-100}"
DURATION="${DURATION:-30s}"
RATE="${RATE:-400}"
DIST="${DIST:-fixed}"

# defining output and run-specific settings
OUTPUT_DIR="${OUTPUT_DIR:-output}"
RUN_NAME="${RUN_NAME:-burst_$(date +%Y%m%d_%H%M%S)}"
ARRIVAL_COUNTS_SOURCE="${ARRIVAL_COUNTS_SOURCE:-arrival_counts.csv}"

# Logging the configuration and run details
echo "Running wrk2 against burst-server"
echo "  url=${URL}"
echo "  threads=${THREADS} connections=${CONNECTIONS} duration=${DURATION}"
echo "  rate=${RATE} req/s dist=${DIST}"
echo "  output=${OUTPUT_DIR}/${RUN_NAME}"

# create output directory for this run
mkdir -p "${OUTPUT_DIR}/${RUN_NAME}"
run_dir="${OUTPUT_DIR}/${RUN_NAME}/conn${CONNECTIONS}"
mkdir -p "${run_dir}"

echo
echo "============================================================"
echo "Running connections=${CONNECTIONS}"
echo "============================================================"

# save the run configuration
{
  echo "url=${URL}"
  echo "threads=${THREADS}"
  echo "connections=${CONNECTIONS}"
  echo "duration=${DURATION}"
  echo "rate=${RATE}"
  echo "dist=${DIST}"
} > "${run_dir}/run.info"


# location of the wrk executable
WRK_BIN="${WRK_BIN:-./DeathStarBench/wrk2/wrk}"

# checking if it exists
if [[ ! -x "$WRK_BIN" ]]; then
  echo "wrk executable not found or not executable: $WRK_BIN" >&2
  exit 1
fi

set +e
"$WRK_BIN" \
  -t"${THREADS}" \
  -c"${CONNECTIONS}" \
  -d"${DURATION}" \
  -R"${RATE}" \
  -D"${DIST}" \
  --latency \
  --requests \
  "${URL}" 2>&1 | tee "${run_dir}/wrk_output.txt"
status=${PIPESTATUS[0]}
set -e

awk '/Latency Distribution \(HdrHistogram/ {printing=1} printing {print}' \
  "${run_dir}/wrk_output.txt" > "${run_dir}/hdr_latency.txt"

# if the arrival counts source file exists, copy it to the output directory
if [[ -f "${ARRIVAL_COUNTS_SOURCE}" ]]; then
  cp "${ARRIVAL_COUNTS_SOURCE}" "${run_dir}/arrival_counts.csv"
  echo "Saved arrivals to ${run_dir}/arrival_counts.csv"
fi

echo "Saved wrk output to ${run_dir}/wrk_output.txt"
echo "Saved HDR latency output to ${run_dir}/hdr_latency.txt"

if (( status != 0 )); then
  exit "${status}"
fi
