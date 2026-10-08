#!/usr/bin/env python3
import psutil
import time
import csv
import sys
import signal

# Handle graceful shutdown when the bash script sends a termination signal
def handle_sigterm(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

output_file = sys.argv[1]
num_cores = psutil.cpu_count()

with open(output_file, mode='w', newline='') as f:
    writer = csv.writer(f)

    # Create headers: timestamp, core_0, core_1, ..., core_N, overall
    headers = ['timestamp_unix'] + [f'core_{i}' for i in range(num_cores)] + ['overall']
    writer.writerow(headers)

    # Initial call to prime the CPU percentage calculation
    psutil.cpu_percent(interval=None, percpu=True)
    psutil.cpu_percent(interval=None)

    try:
        while True:
            # 100ms sampling interval
            time.sleep(0.1)

            timestamp = time.time()
            per_cpu = psutil.cpu_percent(interval=None, percpu=True)
            overall = psutil.cpu_percent(interval=None)

            writer.writerow([timestamp] + per_cpu + [overall])
            f.flush() # Ensure data is written to disk immediately

    except KeyboardInterrupt:
        pass
