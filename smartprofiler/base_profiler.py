import logging
import threading
from abc import ABC, abstractmethod
import os
import json
import csv
from typing import Any, Callable, Dict, List, Optional
from filelock import FileLock, Timeout
from functools import wraps
from .logger_adapter import LoggerAdapter

# Thread-local storage for thread-safe profiling
_thread_local = threading.local()

class BaseProfiler(ABC):
    """Abstract base class for profiling implementations with aggregate statistics."""

    def __init__(self, logger: Optional[Any] = None, log_level: int = logging.INFO, enable_logging: bool = True):
        """
        Initialize the profiler with an optional custom logger, log level, and logging enablement.

        Args:
            logger: Custom logger instance (default: None, uses default logger).
                  Can be logging.Logger, loguru.Logger, structlog.BoundLogger, or any custom logger.
            log_level: Logging level to use (e.g., logging.INFO, logging.DEBUG).
            enable_logging: If False, disables logging of metrics.
        """
        # Create a default logger if none provided
        default_logger = logging.getLogger(__name__)
        if not default_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            default_logger.addHandler(handler)
        
        # Wrap the logger with our adapter
        self.logger = LoggerAdapter(logger or default_logger)
        self.logger.setLevel(log_level)
        self.log_level = log_level
        self.enable_logging = enable_logging
        # Store profiling results for aggregate statistics
        self.stats: List[Dict] = []

    @abstractmethod
    def profile_function(self, func: Callable) -> Callable:
        """Decorator to profile a function."""
        pass

    @abstractmethod
    def profile_block(self, label: str):
        """Context manager to profile a code block."""
        pass

    @abstractmethod
    def profile_line(self, label: str):
        """Context manager to profile a specific line or small block."""
        pass

    def _wrap_function(self, func: Callable, profile_logic: Callable) -> Callable:
        """Helper to wrap a function with profiling logic."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return profile_logic(func, *args, **kwargs)
        return wrapper

    def get_stats(self) -> List[Dict]:
        """Return collected profiling statistics."""
        return self.stats

    def clear_stats(self):
        """Clear collected profiling statistics."""
        self.stats.clear()

    def summarize_stats(self):
        """Log a summary of collected statistics."""
        if not self.enable_logging:
            return
        if not self.stats:
            self.logger.log(self.log_level, "No profiling statistics available.")
            return
        self.logger.log(self.log_level, f"Summary of {len(self.stats)} profiling events:")
        for stat in self.stats:
            self.logger.log(self.log_level, f"{stat['label']}: {stat['metrics']}")

    def export_stats(self, file_path: str, format: str = 'json'):
        """
        Export profiling statistics to a file in the specified format.

        Args:
            file_path (str): The path to the output file.
            format (str): The format for exporting. Can be 'json' or 'csv'.
                          Defaults to 'json'.
        """
        if format not in ['json', 'csv']:
            self.logger.error(f"Unsupported format: '{format}'. Please use 'json' or 'csv'.")
            raise ValueError(f"Unsupported format: '{format}'. Please use 'json' or 'csv'.")

        lock_path = f"{file_path}.lock"
        try:
            with FileLock(lock_path, timeout=10):
                if format == 'json':
                    self._export_to_json(file_path)
                elif format == 'csv':
                    self._export_to_csv(file_path)
        except Timeout:
            self.logger.error(f"Could not acquire lock on {file_path} after 10 seconds. Another process may be holding it.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during export: {e}")
        finally:
            if os.path.exists(lock_path):
                os.remove(lock_path)

    def _export_to_json(self, file_path: str):
        """Private helper method to export stats to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4)
        except (IOError, PermissionError) as e:
            self.logger.error(f"Error writing to JSON file {file_path}: {e}")

    def _export_to_csv(self, file_path: str):
        """Private helper method to export stats to a CSV file."""
        if not self.stats:
            return

        flattened_data = []
        for item in self.stats:
            flat_record = {'label': item.get('label')}
            flat_record.update(item.get('metrics', {}))
            flattened_data.append(flat_record)

        header_fields = set(['label'])
        for record in flattened_data:
            header_fields.update(record.keys())
        
        sorted_header = sorted(list(header_fields), key=lambda x: (x != 'label', x))

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_header)
                writer.writeheader()
                writer.writerows(flattened_data)
        except (IOError, PermissionError) as e:
            self.logger.error(f"Error writing to CSV file {file_path}: {e}")
