import matplotlib.pyplot as plt
import numpy as np
import os
from .base_profiler import BaseProfiler


def plot_profiling_stats(
    profiling_results: list,
    title: str = "Profiling Statistics",
    metric_threshold: dict = None,
    exclude_zero: bool = True,
    bar_colors: list = None,
    use_log_scale: bool = False,
    output_path: str = None,
):
    """
    Generates a bar plot of profiling statistics with advanced filtering and customization.

    This function is backward-compatible and can accept either a list of profiler objects
    (e.g., CPUProfiler) or a list of raw statistics dictionaries.

    Args:
        profiling_results (list): A list of profiler objects or raw statistics dictionaries.
        title (str, optional): The title of the plot. Defaults to "Profiling Statistics".
        metric_threshold (dict, optional): A dictionary to filter metrics by a minimum value.
                                           Example: {'execution_time': 0.1}. Defaults to None.
        exclude_zero (bool, optional): If True, metrics with a value of zero are excluded.
                                       Defaults to True.
        bar_colors (list, optional): A list of colors for the bars. If not provided, a default
                                     colormap will be used. Defaults to None.
        use_log_scale (bool, optional): If True, the y-axis will use a logarithmic scale.
                                        Defaults to False.
        output_path (str, optional): The full path to save the plot file (e.g., 'plots/my_plot.png').
                                     If not provided, the plot is displayed interactively. Defaults to None.
    """
    if not profiling_results:
        print("No profiling results to plot.")
        return

    raw_stats = []
    # Check if input is a list of profiler objects for backward compatibility
    if profiling_results and isinstance(profiling_results[0], BaseProfiler):
        for profiler in profiling_results:
            raw_stats.extend(profiler.get_stats())
    else:
        # Otherwise, assume it's already a list of stats
        raw_stats = profiling_results

    if not raw_stats:
        print("No profiling data to plot.")
        return

    # Helper to flatten nested metric dictionaries
    def _flatten_metrics(metrics: dict, parent_key: str = ''):
        items = []
        for k, v in metrics.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(_flatten_metrics(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # Process raw_stats to flatten metrics
    processed_stats = []
    for record in raw_stats:
        processed_stats.append({
            'label': record['label'],
            'metrics': _flatten_metrics(record.get('metrics', {}))
        })

    # Filter stats based on threshold and zero-value exclusion
    filtered_stats = []
    if metric_threshold is None:
        metric_threshold = {}

    for record in processed_stats:
        metrics = record.get("metrics", {})
        filtered_metrics = {}

        for metric, value in metrics.items():
            if exclude_zero and value == 0:
                continue
            if metric in metric_threshold and value < metric_threshold[metric]:
                continue
            filtered_metrics[metric] = value

        if filtered_metrics:
            filtered_stats.append(
                {"label": record["label"], "metrics": filtered_metrics}
            )

    if not filtered_stats:
        print("No data available to plot after applying filters.")
        return

    labels = [record["label"] for record in filtered_stats]
    all_metrics = sorted(list(set(m for record in filtered_stats for m in record["metrics"])))

    if not all_metrics:
        print("No metrics to plot after filtering.")
        return

    # Prepare data for grouped bar chart
    metric_values = {metric: [record["metrics"].get(metric, 0) for record in filtered_stats] for metric in all_metrics}

    x = np.arange(len(labels))
    n_metrics = len(all_metrics)
    width = 0.8 / n_metrics
    fig, ax = plt.subplots(figsize=(max(12, len(labels) * 1.5), 8))

    if bar_colors is None:
        colors = plt.cm.viridis(np.linspace(0, 1, n_metrics))
    else:
        colors = [bar_colors[i % len(bar_colors)] for i in range(n_metrics)]

    for i, metric in enumerate(all_metrics):
        offset = (i - n_metrics / 2 + 0.5) * width
        rects = ax.bar(x + offset, metric_values[metric], width, label=metric, color=colors[i])
        ax.bar_label(rects, padding=3, fmt='%.2g')

    # Configure plot aesthetics
    ax.set_ylabel("Values")
    ax.set_title(title)
    ax.set_xticks(x, labels, rotation=45, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    if use_log_scale:
        ax.set_yscale("log")
        ax.set_ylabel("Values (Log Scale)")

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()

    # Save to file or show interactively
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plt.savefig(output_path, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
        plt.close(fig)
    else:
        plt.show()
