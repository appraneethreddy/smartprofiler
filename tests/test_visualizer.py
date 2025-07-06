import unittest
from unittest.mock import patch, MagicMock
import os
from smartprofiler.visualizer import plot_profiling_stats
from smartprofiler.base_profiler import BaseProfiler

# Sample statistics for testing
SAMPLE_STATS = [
    {
        'label': 'FunctionA',
        'metrics': {'execution_time': 0.5, 'memory_usage': 10, 'io_ops': 0}
    },
    {
        'label': 'FunctionB',
        'metrics': {'execution_time': 0.1, 'memory_usage': 5, 'io_ops': 20}
    },
    {
        'label': 'FunctionC',
        'metrics': {'execution_time': 0.8, 'memory_usage': 0, 'io_ops': 30}
    }
]

class TestVisualizer(unittest.TestCase):

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_plot_with_defaults(self, mock_subplots, mock_show):
        """Test plotting with default options (exclude_zero=True)."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)

        plot_profiling_stats(SAMPLE_STATS)

        mock_subplots.assert_called_once()
        mock_show.assert_called_once()

        # Three unique metrics remain after filtering zeros: execution_time, io_ops, memory_usage
        self.assertEqual(mock_ax.bar.call_count, 3)
        mock_ax.set_yscale.assert_not_called()

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_exclude_zero_metrics_false(self, mock_subplots, mock_show):
        """Test plotting when exclude_zero is False."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)

        plot_profiling_stats(SAMPLE_STATS, exclude_zero=False)
        
        # All 3 metrics should be plotted
        self.assertEqual(mock_ax.bar.call_count, 3)

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_metric_threshold(self, mock_subplots, mock_show):
        """Test filtering metrics based on a threshold."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)

        plot_profiling_stats(SAMPLE_STATS, metric_threshold={'execution_time': 0.6})

        # Check that the data for 'execution_time' bar plot is filtered
        # The call for execution_time should be the first one (sorted alphabetically)
        args, _ = mock_ax.bar.call_args_list[0]
        data = args[1]
        self.assertListEqual(list(data), [0, 0, 0.8])

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_log_scale(self, mock_subplots, mock_show):
        """Test enabling the logarithmic scale."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)

        plot_profiling_stats(SAMPLE_STATS, use_log_scale=True)

        mock_ax.set_yscale.assert_called_once_with('log')

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_custom_bar_colors(self, mock_subplots, mock_show):
        """Test using custom colors for bars."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)
        
        custom_colors = ['red', 'green', 'blue']
        plot_profiling_stats(SAMPLE_STATS, bar_colors=custom_colors)

        self.assertEqual(mock_ax.bar.call_count, 3)
        self.assertEqual(mock_ax.bar.call_args_list[0].kwargs['color'], 'red')
        self.assertEqual(mock_ax.bar.call_args_list[1].kwargs['color'], 'green')
        self.assertEqual(mock_ax.bar.call_args_list[2].kwargs['color'], 'blue')

    @patch('builtins.print')
    @patch('matplotlib.pyplot.show')
    def test_no_data_to_plot(self, mock_show, mock_print):
        """Test that nothing is plotted if stats are empty."""
        plot_profiling_stats([])
        mock_print.assert_called_once_with("No profiling results to plot.")
        mock_show.assert_not_called()

    @patch('builtins.print')
    @patch('matplotlib.pyplot.show')
    def test_all_data_filtered(self, mock_show, mock_print):
        """Test that nothing is plotted if all data is filtered out."""
        plot_profiling_stats(SAMPLE_STATS, metric_threshold={'execution_time': 1.0, 'memory_usage': 100, 'io_ops': 100})
        mock_print.assert_called_once_with("No data available to plot after applying filters.")
        mock_show.assert_not_called()

    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_plot_with_profiler_objects(self, mock_subplots, mock_show):
        """Test backward compatibility with profiler objects."""
        mock_ax = MagicMock()
        mock_subplots.return_value = (MagicMock(), mock_ax)

        # Create mock profiler objects
        mock_profiler1 = MagicMock(spec=BaseProfiler)
        mock_profiler1.get_stats.return_value = [SAMPLE_STATS[0]]
        mock_profiler2 = MagicMock(spec=BaseProfiler)
        mock_profiler2.get_stats.return_value = [SAMPLE_STATS[1], SAMPLE_STATS[2]]

        plot_profiling_stats([mock_profiler1, mock_profiler2])

        mock_subplots.assert_called_once()
        mock_show.assert_called_once()
        self.assertEqual(mock_ax.bar.call_count, 3)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.show')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    def test_plot_saving_to_file(self, mock_exists, mock_makedirs, mock_show, mock_close, mock_savefig):
        """Test saving the plot to a file."""
        output_path = os.path.join('test_images', 'test_plot.png')

        plot_profiling_stats(SAMPLE_STATS, output_path=output_path)

        mock_exists.assert_called_once_with('test_images')
        mock_makedirs.assert_called_once_with('test_images')
        mock_savefig.assert_called_once_with(output_path, bbox_inches='tight')
        mock_close.assert_called_once()
        mock_show.assert_not_called()


if __name__ == '__main__':
    unittest.main()
