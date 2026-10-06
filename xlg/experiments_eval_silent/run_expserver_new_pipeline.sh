#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
EXPSERVER_RPS_LIST="${EXPSERVER_RPS_LIST:-1000 2000 3000}"
EXPSERVER_RESULTS_ROOT="${EXPSERVER_RESULTS_ROOT:-${REPO_ROOT}/ExpServer_new_results}"

GLOBAL_DURATION="${DURATION:-}"
STAGE_A_DURATION="${STAGE_A_DURATION:-${GLOBAL_DURATION:-20s}}"
STAGE_B_BASELINE_DURATION="${STAGE_B_BASELINE_DURATION:-${GLOBAL_DURATION:-30s}}"
STAGE_B_CONDITIONS_DURATION="${STAGE_B_CONDITIONS_DURATION:-${GLOBAL_DURATION:-30s}}"
NORMAL_NETWORK_DELAY="${NORMAL_NETWORK_DELAY:-5ms}"
DEGRADED_NETWORK_DELAY="${DEGRADED_NETWORK_DELAY:-15ms}"
FASTER_NETWORK_DELAY="${FASTER_NETWORK_DELAY:-0ms}"
EXPSERVER_NETWORK_SCHEDULE="${EXPSERVER_NETWORK_SCHEDULE:-5ms:5 8ms:4 0ms:4 10ms:4 0ms:3 30ms:4 0ms:6}" 
STAGE_B_SEVERITIES="${STAGE_B_SEVERITIES:-mild mod severe}"
NUM_EVAL_RUNS="${NUM_EVAL_RUNS:-1}"
NUM_CONTROL_RUNS="${NUM_CONTROL_RUNS:-3}"
CPU_CONTENTION_START_DELAY="${CPU_CONTENTION_START_DELAY:-5s}"

cpuset_for_rps() {
  local rps="$1"
  local override_var="EXPSERVER_CPUSET_RPS_${rps}"
  local override_value="${!override_var:-}"

  if [[ -n "${EXPSERVER_CPUSET:-}" ]]; then
    echo "$EXPSERVER_CPUSET"
    return 0
  fi

  if [[ -n "$override_value" ]]; then
    echo "$override_value"
    return 0
  fi

  case "$rps" in
    1000) echo "0-1" ;;
    2000) echo "0-3" ;;
    3000) echo "0-7" ;;
    *) echo "0-7" ;;
  esac
}

require_targets_file "$TARGETS_FILE"
mkdir -p "$EXPSERVER_RESULTS_ROOT"

for rps in $EXPSERVER_RPS_LIST; do
  rps_dir="${EXPSERVER_RESULTS_ROOT}/rps_${rps}"
  stage_a_dir="${rps_dir}/stage_a"
  stage_b_dir="${rps_dir}/stage_b_baseline"
  eval_cpuset="${EVAL_CPUSET:-${EXPSERVER_CPUSET:-0-7}}"
  cpu_contention_cpuset="$(cpuset_for_rps "$rps")"

  if [[ -d "$rps_dir" ]] && [[ -n "$(find "$rps_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "Refusing to write into non-empty results directory: ${rps_dir}" >&2
    exit 1
  fi

  mkdir -p "$rps_dir"

  log "ExpServer new evaluation rps=${rps} cpuset=${eval_cpuset} cpu_contention_cpuset=${cpu_contention_cpuset} output=${rps_dir}"
  PYTHON_BIN="$PYTHON_BIN" \
  BASELINE_RPS="$rps" \
  TARGET_RPS="$rps" \
  STAGE_B_RPS="$rps" \
  RATE="$rps" \
  EVAL_RATE="$rps" \
  STAGE_A_DURATION="$STAGE_A_DURATION" \
  STAGE_B_BASELINE_DURATION="$STAGE_B_BASELINE_DURATION" \
  STAGE_B_CONDITIONS_DURATION="$STAGE_B_CONDITIONS_DURATION" \
  NORMAL_NETWORK_DELAY="$NORMAL_NETWORK_DELAY" \
  DEGRADED_NETWORK_DELAY="$DEGRADED_NETWORK_DELAY" \
  FASTER_NETWORK_DELAY="$FASTER_NETWORK_DELAY" \
  EXPSERVER_NETWORK_SCHEDULE="$EXPSERVER_NETWORK_SCHEDULE" \
  STAGE_B_SEVERITIES="$STAGE_B_SEVERITIES" \
  NUM_EVAL_RUNS="$NUM_EVAL_RUNS" \
  NUM_CONTROL_RUNS="$NUM_CONTROL_RUNS" \
  CPU_CONTENTION_START_DELAY="$CPU_CONTENTION_START_DELAY" \
  CPU_CONTENTION_CPUSET="$cpu_contention_cpuset" \
  EVAL_CPUSET="$eval_cpuset" \
  STAGE_A_DIR="$stage_a_dir" \
  STAGE_B_DIR="$stage_b_dir" \
  "${SCRIPT_DIR}/run_full_pipeline.sh"

  cat > "${rps_dir}/expserver_run_config.env" <<EOF
rps=${rps}
stage_a_duration=${STAGE_A_DURATION}
stage_b_baseline_duration=${STAGE_B_BASELINE_DURATION}
stage_b_conditions_duration=${STAGE_B_CONDITIONS_DURATION}
normal_network_delay=${NORMAL_NETWORK_DELAY}
degraded_network_delay=${DEGRADED_NETWORK_DELAY}
faster_network_delay=${FASTER_NETWORK_DELAY}
network_schedule=${EXPSERVER_NETWORK_SCHEDULE}
stage_b_severities=${STAGE_B_SEVERITIES}
num_eval_runs=${NUM_EVAL_RUNS}
num_control_runs=${NUM_CONTROL_RUNS}
cpu_contention_start_delay=${CPU_CONTENTION_START_DELAY}
eval_cpuset=${eval_cpuset}
cpu_contention_cpuset=${cpu_contention_cpuset}
stage_a_dir=${stage_a_dir}
stage_b_dir=${stage_b_dir}
EOF
done

log "ExpServer new evaluation complete: ${EXPSERVER_RESULTS_ROOT}"
