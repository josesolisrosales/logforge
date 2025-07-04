"""High-performance log generator core."""

import os
import gzip
import bz2
import lzma
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Union, TextIO
import random
import time
from collections import defaultdict
import sys

import numpy as np
from faker import Faker

from logsmith.core.config import LogConfig
from logsmith.core.formats import FormatterFactory, LogFormat
from logsmith.generators.data import DataGenerator
from logsmith.utils.performance import PerformanceMonitor


class LogGenerator:
    """High-performance log generator."""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.formatter = FormatterFactory.create_formatter(config.output.format)
        self.data_generator = DataGenerator(config)
        self.performance_monitor = PerformanceMonitor()
        self.fake = Faker()
        
        # Pre-compute values for better performance
        self._precompute_data()
    
    def _precompute_data(self):
        """Pre-compute data for better performance."""
        # Pre-compute log levels based on distribution
        self.log_levels = []
        self.log_level_weights = []
        
        for level, weight in self.config.level_distribution.levels.items():
            self.log_levels.append(level)
            self.log_level_weights.append(weight)
        
        # Pre-compute timestamps if enabled
        if self.config.performance.precompute_timestamps:
            self.timestamps = self._generate_timestamps()
        else:
            self.timestamps = None
    
    def _generate_timestamps(self) -> np.ndarray:
        """Pre-generate timestamps for better performance."""
        start_time = self.config.get_effective_start_time()
        end_time = self.config.get_effective_end_time()
        total_seconds = (end_time - start_time).total_seconds()
        
        if self.config.time.interval == "uniform":
            # Uniform distribution
            timestamps = np.random.uniform(0, total_seconds, self.config.total_logs)
        elif self.config.time.interval == "exponential":
            # Exponential distribution (bursty traffic)
            timestamps = np.random.exponential(total_seconds / self.config.total_logs, 
                                             self.config.total_logs)
            timestamps = np.clip(timestamps, 0, total_seconds)
        elif self.config.time.interval == "normal":
            # Normal distribution (centered around middle)
            timestamps = np.random.normal(total_seconds / 2, total_seconds / 6, 
                                        self.config.total_logs)
            timestamps = np.clip(timestamps, 0, total_seconds)
        else:
            # Regular interval with jitter
            base_interval = total_seconds / self.config.total_logs
            timestamps = np.arange(0, total_seconds, base_interval)[:self.config.total_logs]
            
            # Add jitter
            if self.config.time.jitter > 0:
                jitter_range = base_interval * self.config.time.jitter
                jitter = np.random.uniform(-jitter_range, jitter_range, len(timestamps))
                timestamps += jitter
                timestamps = np.clip(timestamps, 0, total_seconds)
        
        # Sort timestamps
        timestamps.sort()
        
        # Convert to datetime objects
        return np.array([start_time + timedelta(seconds=float(ts)) for ts in timestamps])
    
    def generate_single_log(self, timestamp: Optional[datetime] = None, 
                           level: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single log entry."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if level is None:
            level = random.choices(self.log_levels, weights=self.log_level_weights)[0]
        
        # Generate base log entry
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": self.data_generator.generate_message(level),
        }
        
        # Add format-specific fields
        if self.config.output.format in ["apache_common", "apache_combined", "nginx"]:
            log_entry.update(self.data_generator.generate_web_log_fields())
        elif self.config.output.format == "syslog":
            log_entry.update(self.data_generator.generate_syslog_fields())
        
        # Add custom fields
        log_entry.update(self.config.custom_fields)
        
        # Add generated fields
        log_entry.update(self.data_generator.generate_additional_fields())
        
        return log_entry
    
    def generate_batch(self, batch_size: int, 
                      start_idx: int = 0) -> Iterator[Dict[str, Any]]:
        """Generate a batch of log entries."""
        for i in range(batch_size):
            idx = start_idx + i
            
            # Use pre-computed timestamp if available
            if self.timestamps is not None and idx < len(self.timestamps):
                timestamp = self.timestamps[idx]
            else:
                timestamp = None
            
            yield self.generate_single_log(timestamp=timestamp)
    
    def _format_batch(self, batch: List[Dict[str, Any]]) -> List[str]:
        """Format a batch of log entries."""
        return [self.formatter.format(entry) for entry in batch]
    
    def _write_batch(self, formatted_logs: List[str], 
                    output_file: TextIO) -> None:
        """Write a batch of formatted logs to file."""
        for log_line in formatted_logs:
            output_file.write(log_line + '\n')
    
    def _get_output_file(self, file_path: Optional[Path] = None) -> TextIO:
        """Get output file handle with compression support."""
        if file_path is None:
            return sys.stdout
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle compression
        if self.config.output.compression == "gzip":
            return gzip.open(file_path, 'wt', encoding='utf-8')
        elif self.config.output.compression == "bz2":
            return bz2.open(file_path, 'wt', encoding='utf-8')
        elif self.config.output.compression == "lzma":
            return lzma.open(file_path, 'wt', encoding='utf-8')
        else:
            return open(file_path, 'w', encoding='utf-8', 
                       buffering=self.config.output.buffer_size)
    
    def generate_sequential(self, progress_callback: Optional[callable] = None) -> None:
        """Generate logs sequentially (single-threaded)."""
        self.performance_monitor.start_generation()
        
        try:
            with self._get_output_file(self.config.output.file_path) as output_file:
                # Write headers if needed
                headers = self.formatter.get_headers()
                if headers:
                    output_file.write(headers + '\n')
                
                batch_size = self.config.performance.batch_size
                total_logs = self.config.total_logs
                
                for batch_start in range(0, total_logs, batch_size):
                    current_batch_size = min(batch_size, total_logs - batch_start)
                    
                    # Generate batch
                    batch = list(self.generate_batch(current_batch_size, batch_start))
                    
                    # Format batch
                    formatted_logs = self._format_batch(batch)
                    
                    # Write batch
                    self._write_batch(formatted_logs, output_file)
                    
                    # Progress callback
                    if progress_callback:
                        progress = (batch_start + current_batch_size) / total_logs
                        progress_callback(progress, batch_start + current_batch_size)
                    
                    # Force flush for better performance monitoring
                    if batch_start % (batch_size * 10) == 0:
                        output_file.flush()
        
        finally:
            self.performance_monitor.end_generation()
    
    def generate_parallel(self, progress_callback: Optional[callable] = None) -> None:
        """Generate logs in parallel using multiple processes."""
        self.performance_monitor.start_generation()
        
        try:
            # Determine number of workers
            workers = self.config.performance.workers
            if workers is None:
                workers = min(mp.cpu_count(), 8)  # Cap at 8 for memory reasons
            
            batch_size = self.config.performance.batch_size
            total_logs = self.config.total_logs
            
            # Prepare work batches
            import json
            # Serialize config to JSON to avoid pickling issues
            config_json = json.dumps(self.config.dict(), default=str)
            
            work_batches = []
            for batch_start in range(0, total_logs, batch_size):
                current_batch_size = min(batch_size, total_logs - batch_start)
                work_batches.append((current_batch_size, batch_start, config_json))
            
            with self._get_output_file(self.config.output.file_path) as output_file:
                # Write headers if needed
                headers = self.formatter.get_headers()
                if headers:
                    output_file.write(headers + '\n')
                
                # Process batches in parallel
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    completed_logs = 0
                    
                    for formatted_batch in executor.map(_generate_worker_batch, 
                                                      work_batches):
                        # Write batch
                        self._write_batch(formatted_batch, output_file)
                        
                        completed_logs += len(formatted_batch)
                        
                        # Progress callback
                        if progress_callback:
                            progress = completed_logs / total_logs
                            progress_callback(progress, completed_logs)
                        
                        # Periodic flush
                        if completed_logs % (batch_size * 10) == 0:
                            output_file.flush()
        
        finally:
            self.performance_monitor.end_generation()

    def generate(self, progress_callback: Optional[callable] = None) -> None:
        """Generate logs (automatically choose sequential or parallel)."""
        # Use parallel generation for large datasets
        if (self.config.total_logs > 100000 and 
            self.config.performance.workers != 1):
            self.generate_parallel(progress_callback)
        else:
            self.generate_sequential(progress_callback)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.performance_monitor.get_stats()

    def estimate_generation_time(self) -> float:
        """Estimate total generation time in seconds."""
        # Rough estimate based on log count and format complexity
        base_time_per_log = 0.0001  # 0.1ms per log (baseline)
        
        # Format complexity multiplier
        format_multipliers = {
            LogFormat.JSON: 1.2,
            LogFormat.STANDARD: 1.0,
            LogFormat.APACHE_COMMON: 1.5,
            LogFormat.APACHE_COMBINED: 1.8,
            LogFormat.SYSLOG: 1.3,
            LogFormat.CSV: 1.1,
            LogFormat.GELF: 1.4,
            LogFormat.CEF: 1.6,
        }
        
        format_multiplier = format_multipliers.get(
            LogFormat(self.config.output.format), 1.0
        )
        
        estimated_time = (self.config.total_logs * base_time_per_log * 
                         format_multiplier)
        
        # Adjust for parallel processing
        if self.config.performance.workers and self.config.performance.workers > 1:
            estimated_time /= min(self.config.performance.workers, mp.cpu_count())
        
        return estimated_time

    def validate_config(self) -> List[str]:
        """Validate configuration and return any warnings."""
        warnings = []
        
        # Check for performance issues
        if self.config.total_logs > 1000000 and self.config.performance.batch_size < 10000:
            warnings.append("Small batch size may impact performance for large log counts")
        
        # Check memory usage (only for large datasets)
        if self.config.total_logs > 500000:  # Only check for datasets > 500K logs
            workers = self.config.performance.workers or 1
            # More realistic estimate: batch_size * workers * 2KB per log entry (JSON overhead)
            estimated_memory_mb = (self.config.performance.batch_size * workers * 2) / 1024  # MB
            if estimated_memory_mb > 512:  # 512MB threshold (more realistic)
                warnings.append(f"High memory usage expected (~{estimated_memory_mb:.0f}MB) - consider reducing batch size or workers")
        
        # Check file size
        if self.config.output.file_path:
            estimated_size = self.config.total_logs * 200  # Rough estimate (200 bytes per log)
            if estimated_size > 10 * 1024 * 1024 * 1024:  # 10GB
                warnings.append("Large output file expected - consider enabling compression")
        
        return warnings


def _generate_worker_batch(args: tuple) -> List[str]:
    """Worker function for parallel generation."""
    batch_size, start_idx, config_json = args
    
    # Recreate config and generator in worker process
    import json
    config_dict = json.loads(config_json)
    config = LogConfig(**config_dict)
    generator = LogGenerator(config)
    
    # Generate and format batch
    batch = list(generator.generate_batch(batch_size, start_idx))
    return generator._format_batch(batch)