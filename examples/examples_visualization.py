import time
import random
import requests
import logging
import tempfile
import os
from smartprofiler import CPUProfiler, DiskProfiler, FunctionProfiler, MemoryProfiler, NetworkProfiler, plot_profiling_stats

def main():
    # Set up a logger for minimal output
    logger = logging.getLogger('smartprofiler_visualization')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    temp_dir = tempfile.gettempdir()

    # --- Example 1: CPU, Disk, and Memory Profiling ---
    print("--- Running CPU, Disk, and Memory Profiling Examples ---")
    cpu_profiler = CPUProfiler(time_func='execution_time', logger=logger)
    disk_profiler = DiskProfiler(disk_path=temp_dir, disk_metrics={'write_bytes': True}, logger=logger)
    mem_profiler = MemoryProfiler(logger=logger)

    @cpu_profiler.profile_function
    @mem_profiler.profile_function
    def matrix_multiply():
        size = 200  # Reduced size for faster example execution
        matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
        matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
        result = [[0 for _ in range(size)] for _ in range(size)]
        for i in range(size):
            for j in range(size):
                for k in range(size):
                    result[i][j] += matrix_a[i][k] * matrix_b[k][j]

    @disk_profiler.profile_function
    def write_large_file():
        with open(os.path.join(temp_dir, 'large_file.txt'), 'w') as f:
            f.write("Sample data" * 1000)

    @mem_profiler.profile_function
    def allocate_large_list():
        _ = [0] * (10**6)  # Allocate 1 million integers

    # Run the examples
    matrix_multiply()
    write_large_file()
    allocate_large_list()

    # Combine stats from all profilers
    all_stats = cpu_profiler.get_stats() + disk_profiler.get_stats() + mem_profiler.get_stats()

    # --- Generate Visualizations for Example 1 ---
    print("\n--- Visualizations for CPU, Disk, and Memory ---")
    print("NOTE: You must close each plot window to proceed to the next one.")

    # 1. Default plot (zeros excluded)
    print("\n1. Displaying default plot (zero-value metrics are hidden)...")
    plot_profiling_stats(
        all_stats,
        title="CPU, Disk & Memory Profile (Default)"
    )

    # 2. Plot with a threshold
    print("\n2. Displaying plot with a threshold (execution_time > 0.1s)...")
    plot_profiling_stats(
        all_stats,
        title="Profile with Execution Time > 0.1s",
        metric_threshold={'execution_time': 0.1}
    )

    # 3. Plot with log scale and custom colors
    print("\n3. Displaying plot with log scale and custom colors...")
    plot_profiling_stats(
        all_stats,
        title="Profile with Log Scale and Custom Colors",
        use_log_scale=True,
        bar_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    )

    # 4. Backward-compatible: passing profiler objects and saving to file
    print("\n4. Saving plot to file by passing profiler objects (backward-compatible)...")
    output_dir = os.path.join(temp_dir, "profiling_images")
    output_path = os.path.join(output_dir, "cpu_disk_mem_profile.png")
    plot_profiling_stats(
        [cpu_profiler, disk_profiler, mem_profiler],
        title="CPU, Disk & Memory Profile (Saved to File)",
        output_path=output_path
    )

    # --- Example 2: Network and Function Call Profiling ---
    print("\n--- Running Network and Function Call Profiling Examples ---")
    func_profiler = FunctionProfiler(logger=logger)
    net_profiler = NetworkProfiler(network_metrics={'bytes_sent': True, 'bytes_recv': True}, logger=logger)

    @net_profiler.profile_function
    def fetch_multiple_apis():
        urls = ['https://api.github.com', 'https://jsonplaceholder.typicode.com/posts']
        for url in urls:
            try:
                response = requests.get(url, stream=True, timeout=5)
                response.raw.read(1024 * 2)  # Read some data
            except requests.RequestException as e:
                logger.warning(f"Could not fetch {url}: {e}")

    @func_profiler.profile_function
    def recursive_fibonacci(n):
        if n <= 1:
            return n
        return recursive_fibonacci(n-1) + recursive_fibonacci(n-2)

    # Run the examples
    fetch_multiple_apis()
    recursive_fibonacci(10)

    # Combine stats
    all_stats_2 = func_profiler.get_stats() + net_profiler.get_stats()

    def aggregate_stats_by_label(stats_list: list) -> list:
        """Aggregates a list of statistics by their label, summing numeric metrics."""
        aggregated = {}
        for stat in stats_list:
            label = stat['label']
            if label not in aggregated:
                aggregated[label] = {'label': label, 'metrics': {}}
            
            for metric, value in stat['metrics'].items():
                if isinstance(value, (int, float)):
                    aggregated[label]['metrics'].setdefault(metric, 0)
                    aggregated[label]['metrics'][metric] += value
        return list(aggregated.values())

    aggregated_stats_2 = aggregate_stats_by_label(all_stats_2)

    # --- Generate Visualizations for Example 2 ---
    print("\n--- Visualizations for Network and Function Calls ---")

    # 1. Plot aggregated stats
    print("\n1. Displaying plot of aggregated stats...")
    plot_profiling_stats(
        aggregated_stats_2,
        title="Aggregated Profile of Network and Function Calls",
        exclude_zero=False
    )

if __name__ == "__main__":
    main()
