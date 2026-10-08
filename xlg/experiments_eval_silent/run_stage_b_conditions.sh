#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# default parameters
DURATION="${DURATION:-30s}"
NUM_EVAL_RUNS="${NUM_EVAL_RUNS:-1}"
STAGE_B_SEVERITIES="${STAGE_B_SEVERITIES:-mild mod severe}"
NORMAL_NETWORK_DELAY="${NORMAL_NETWORK_DELAY:-5ms}"
DEGRADED_NETWORK_DELAY="${DEGRADED_NETWORK_DELAY:-10ms}"
FASTER_NETWORK_DELAY="${FASTER_NETWORK_DELAY:-0ms}"
CPU_CONTENTION_START_DELAY="${CPU_CONTENTION_START_DELAY:-5s}"
CPU_CONTENTION_CPUSET="${CPU_CONTENTION_CPUSET:-$EVAL_CPUSET}"
NUM_CONTROL_RUNS="${NUM_CONTROL_RUNS:-3}"

# what we are ramping up to
BOTTLENECK_RAMP_EXTRA_DELAY="${BOTTLENECK_RAMP_EXTRA_DELAY:-10ms}"
BOTTLENECK_RAMP_INCREMENT="${BOTTLENECK_RAMP_INCREMENT:-3ms}"
BOTTLENECK_RAMP_DURATION="${BOTTLENECK_RAMP_DURATION:-$(subtract_time_values "$DURATION" "5s")}"

# getting the latest stage A and stage B runs
STAGE_A_ROOT="${STAGE_A_ROOT:-${OUTPUT_ROOT}/stage_a_fixed}"
STAGE_A_DIR="${STAGE_A_DIR:-$(ls -d "$STAGE_A_ROOT"/run_* | sort | tail -n 1)}"
STAGE_B_ROOT="${STAGE_B_ROOT:-${OUTPUT_ROOT}/stage_b_variable}"
STAGE_B_DIR="${STAGE_B_DIR:-$(ls -d "$STAGE_B_ROOT"/run_* | sort | tail -n 1)}"
STAGE_B_SETTINGS_JSON="${STAGE_B_SETTINGS_JSON:-${REFERENCE_JSON:-${STAGE_B_DIR}/stage_b_reference.json}}"
CONDITIONS_DIR="${CONDITIONS_DIR:-${STAGE_B_DIR}/conditions}"
CONTROLS_DIR="${CONTROLS_DIR:-${STAGE_B_DIR}/controls}"

# we start at the normal delay and ramp up to normal + extra delay
BOTTLENECK_RAMP_START_DELAY="$NORMAL_NETWORK_DELAY"
BOTTLENECK_RAMP_END_DELAY="$(add_time_values "$NORMAL_NETWORK_DELAY" "$BOTTLENECK_RAMP_EXTRA_DELAY")"

trap 'stop_cpu_stress; stop_client_network_delay_ramps; clear_client_network_delay; stop_sudo_keepalive' EXIT

mkdir -p "$CONDITIONS_DIR" "$CONTROLS_DIR"
require_targets_file "$TARGETS_FILE"
start_sudo_keepalive

# obtaining the rate from the settings json
RATE="$(json_value "$STAGE_B_SETTINGS_JSON" "rate")"
EVAL_RATE="${EVAL_RATE:-${TARGET_RPS:-$RATE}}"

# obtaining the reference csv from stage A
STAGE_A_REFERENCE_CSV="${STAGE_A_REFERENCE_CSV:-$(ls "${STAGE_A_DIR}"/reference/window_results_rps*.csv | sort | head -n 1)}"

run_case() {
  # encapsulates the logic to run a single case with the given parameters, including optional CPU stress
  local base_dir="$1"
  local label="$2"
  local workers="$3"
  local max_workers="$4"
  local connections="$5"
  local max_connections="$6"
  local cpu_jobs="${7:-0}"
  local network_schedule="${8:-0}"
  local run_count="${9:-$NUM_EVAL_RUNS}"

  mkdir -p "$base_dir"
  for run_idx in $(seq 1 "$run_count"); do
    local schedule_pid=""
    if (( cpu_jobs > 0 )); then
      start_cpu_stress_after_delay \
        "$cpu_jobs" \
        "$CPU_CONTENTION_START_DELAY" \
        "${base_dir}/stress_run_$(printf '%02d' "$run_idx").log"
    fi
    if [[ "$network_schedule" == "1" ]]; then
      set_client_network_delay "$NORMAL_NETWORK_DELAY"
      start_client_network_delay_schedule_expserver
      schedule_pid="$CLIENT_NETWORK_RAMP_LAST_PID"
    fi
    # run the attack with reference to the stage A results and the specified parameters
    run_attack_to_dir \
      "${base_dir}/run_$(printf '%02d' "$run_idx")" \
      "${label}_run_${run_idx}" \
      "$EVAL_RATE" \
      "$DURATION" \
      "$TARGETS_FILE" \
      "$STAGE_A_REFERENCE_CSV" \
      "$workers" \
      "$max_workers" \
      "$connections" \
      "$max_connections"
    if [[ -n "$schedule_pid" ]]; then
      wait "$schedule_pid"
      NETWORK_RAMP_PIDS=()
      CLIENT_NETWORK_RAMP_LAST_PID=""
    fi
    if (( cpu_jobs > 0 )); then
      stop_cpu_stress
    fi
  done
}

# run the normal and resource-fault conditions first
set_client_network_delay "$NORMAL_NETWORK_DELAY"
run_case \
  "${CONDITIONS_DIR}/NORMAL" \
  "stage_b_NORMAL" \
  "$HEALTHY_WORKERS" \
  "$HEALTHY_MAX_WORKERS" \
  "$HEALTHY_CONNECTIONS" \
  "$HEALTHY_MAX_CONNECTIONS"

# run CPU contention conditions with varying severity
set_client_network_delay "$NORMAL_NETWORK_DELAY"
DEFAULT_EVAL_CPUSET="$EVAL_CPUSET"
EVAL_CPUSET="$CPU_CONTENTION_CPUSET"
for severity in $STAGE_B_SEVERITIES; do
  run_case \
    "${CONDITIONS_DIR}/CPU_CONTENTION/${severity}" \
    "stage_b_CPU_CONTENTION_${severity}" \
    "$HEALTHY_WORKERS" \
    "$HEALTHY_MAX_WORKERS" \
    "$HEALTHY_CONNECTIONS" \
    "$HEALTHY_MAX_CONNECTIONS" \
    "$(json_value "$STAGE_B_SETTINGS_JSON" "severity.cpu.${severity}")"
done
EVAL_CPUSET="$DEFAULT_EVAL_CPUSET"

# run worker condition with varying severity and staged network schedule
for severity in $STAGE_B_SEVERITIES; do
  workers="$(json_value "$STAGE_B_SETTINGS_JSON" "severity.workers.${severity}")"
  run_case \
    "${CONDITIONS_DIR}/FEW_WORKERS/${severity}" \
    "stage_b_FEW_WORKERS_${severity}" \
    "$workers" \
    "$workers" \
    "$HEALTHY_CONNECTIONS" \
    "$HEALTHY_MAX_CONNECTIONS" \
    0 \
    1
done

# run connection condition with varying severity and staged network schedule
for severity in $STAGE_B_SEVERITIES; do
  connections="$(json_value "$STAGE_B_SETTINGS_JSON" "severity.connections.${severity}")"
  run_case \
    "${CONDITIONS_DIR}/FEW_CONNECTIONS/${severity}" \
    "stage_b_FEW_CONNECTIONS_${severity}" \
    "$HEALTHY_WORKERS" \
    "$HEALTHY_MAX_WORKERS" \
    "$connections" \
    "$connections" \
    0 \
    1
done

# collect path-delay and CPU controls outside conditions so evaluation ignores them
run_case \
  "${CONTROLS_DIR}/PATH_SCHEDULE_CONTROL" \
  "stage_b_PATH_SCHEDULE_CONTROL" \
  "$HEALTHY_WORKERS" \
  "$HEALTHY_MAX_WORKERS" \
  "$HEALTHY_CONNECTIONS" \
  "$HEALTHY_MAX_CONNECTIONS" \
  0 \
  1 \
  "$NUM_CONTROL_RUNS"

set_client_network_delay "$NORMAL_NETWORK_DELAY"
run_case \
  "${CONTROLS_DIR}/CPU_CONTROL" \
  "stage_b_CPU_CONTROL" \
  "$HEALTHY_WORKERS" \
  "$HEALTHY_MAX_WORKERS" \
  "$HEALTHY_CONNECTIONS" \
  "$HEALTHY_MAX_CONNECTIONS" \
  0 \
  0 \
  "$NUM_CONTROL_RUNS"

# run degraded with higher client-side network latency
set_client_network_delay "$DEGRADED_NETWORK_DELAY"
run_case \
  "${CONDITIONS_DIR}/SUT_DEGRADED" \
  "stage_b_SUT_DEGRADED" \
  "$HEALTHY_WORKERS" \
  "$HEALTHY_MAX_WORKERS" \
  "$HEALTHY_CONNECTIONS" \
  "$HEALTHY_MAX_CONNECTIONS"

# run faster with client-side network latency removed
set_client_network_delay "$FASTER_NETWORK_DELAY"
run_case \
  "${CONDITIONS_DIR}/SUT_FASTER" \
  "stage_b_SUT_FASTER" \
  "$HEALTHY_WORKERS" \
  "$HEALTHY_MAX_WORKERS" \
  "$HEALTHY_CONNECTIONS" \
  "$HEALTHY_MAX_CONNECTIONS"

# save the configuration for this stage in the conditions directory for reference
cat > "${CONDITIONS_DIR}/run_config.env" <<EOF
stage=stage_b_variable_conditions
rate=${RATE}
eval_rate=${EVAL_RATE}
duration=${DURATION}
num_eval_runs=${NUM_EVAL_RUNS}
num_control_runs=${NUM_CONTROL_RUNS}
stage_b_severities=${STAGE_B_SEVERITIES}
targets_file=${TARGETS_FILE}
normal_network_delay=${NORMAL_NETWORK_DELAY}
degraded_network_delay=${DEGRADED_NETWORK_DELAY}
faster_network_delay=${FASTER_NETWORK_DELAY}
cpu_contention_start_delay=${CPU_CONTENTION_START_DELAY}
cpu_contention_cpuset=${CPU_CONTENTION_CPUSET}
bottleneck_ramp_extra_delay=${BOTTLENECK_RAMP_EXTRA_DELAY}
bottleneck_ramp_duration=${BOTTLENECK_RAMP_DURATION}
bottleneck_ramp_increment=${BOTTLENECK_RAMP_INCREMENT}
bottleneck_ramp_start_delay=${BOTTLENECK_RAMP_START_DELAY}
bottleneck_ramp_end_delay=${BOTTLENECK_RAMP_END_DELAY}
network_schedule=${EXPSERVER_NETWORK_SCHEDULE}
stage_a_dir=${STAGE_A_DIR}
stage_a_reference_csv=${STAGE_A_REFERENCE_CSV}
stage_b_settings_json=${STAGE_B_SETTINGS_JSON}
output_dir=${CONDITIONS_DIR}
controls_dir=${CONTROLS_DIR}
eval_cpuset=${EVAL_CPUSET}
EOF

log "stage B conditions complete: ${CONDITIONS_DIR}"
