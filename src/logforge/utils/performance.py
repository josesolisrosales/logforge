"""Performance monitoring utilities."""

import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

import psutil


class PerformanceMonitor:
    """Monitor performance metrics during log generation."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_logs_generated: int = 0
        self.peak_memory_usage: float = 0
        self.peak_cpu_usage: float = 0
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active: bool = False
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.process = psutil.Process()

    def start_generation(self) -> None:
        """Start performance monitoring."""
        self.start_time = time.time()
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def end_generation(self) -> None:
        """End performance monitoring."""
        self.end_time = time.time()
        self.monitoring_active = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)

    def _monitor_resources(self) -> None:
        """Monitor system resources in background thread."""
        while self.monitoring_active:
            try:
                # Memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)  # RSS in MB
                self.metrics["memory_usage"].append(memory_mb)
                self.peak_memory_usage = max(self.peak_memory_usage, memory_mb)

                # CPU usage
                cpu_percent = self.process.cpu_percent()
                self.metrics["cpu_usage"].append(cpu_percent)
                self.peak_cpu_usage = max(self.peak_cpu_usage, cpu_percent)

                # System-wide metrics
                system_memory = psutil.virtual_memory()
                self.metrics["system_memory_usage"].append(system_memory.percent)

                system_cpu = psutil.cpu_percent()
                self.metrics["system_cpu_usage"].append(system_cpu)

                # I/O statistics (not available on all platforms)
                try:
                    if hasattr(self.process, 'io_counters'):
                        io_counters = self.process.io_counters()
                        self.metrics["read_bytes"].append(io_counters.read_bytes)
                        self.metrics["write_bytes"].append(io_counters.write_bytes)
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    pass

                time.sleep(0.1)  # Sample every 100ms

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.start_time:
            return {"error": "Monitoring not started"}

        duration = (self.end_time or time.time()) - self.start_time

        stats = {
            "duration_seconds": duration,
            "total_logs_generated": self.total_logs_generated,
            "logs_per_second": (
                self.total_logs_generated / duration if duration > 0 else 0
            ),
            "peak_memory_usage_mb": self.peak_memory_usage,
            "peak_cpu_usage_percent": self.peak_cpu_usage,
        }

        # Add aggregated metrics
        for metric_name, values in self.metrics.items():
            if values:
                stats[f"{metric_name}_avg"] = sum(values) / len(values)
                stats[f"{metric_name}_max"] = max(values)
                stats[f"{metric_name}_min"] = min(values)

        return stats

    def log_progress(self, logs_generated: int) -> None:
        """Log progress update."""
        self.total_logs_generated = logs_generated

    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics."""
        if not self.start_time:
            return {"error": "Monitoring not started"}

        current_time = time.time()
        duration = current_time - self.start_time

        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            cpu_percent = self.process.cpu_percent()

            return {
                "duration_seconds": duration,
                "logs_generated": self.total_logs_generated,
                "current_logs_per_second": (
                    self.total_logs_generated / duration if duration > 0 else 0
                ),
                "current_memory_usage_mb": memory_mb,
                "current_cpu_usage_percent": cpu_percent,
                "peak_memory_usage_mb": self.peak_memory_usage,
                "peak_cpu_usage_percent": self.peak_cpu_usage,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"error": "Unable to get process statistics"}

    def format_stats(self) -> str:
        """Format statistics for display."""
        stats = self.get_stats()

        if "error" in stats:
            return f"Error: {stats['error']}"

        lines = [
            "Performance Statistics:",
            f"  Duration: {stats['duration_seconds']:.2f} seconds",
            f"  Total logs: {stats['total_logs_generated']:,}",
            f"  Logs per second: {stats['logs_per_second']:,.0f}",
            f"  Peak memory usage: {stats['peak_memory_usage_mb']:.1f} MB",
            f"  Peak CPU usage: {stats['peak_cpu_usage_percent']:.1f}%",
        ]

        return "\n".join(lines)


class ProgressReporter:
    """Report progress during log generation."""

    def __init__(self, total_logs: int, report_interval: int = 1000):
        self.total_logs = total_logs
        self.report_interval = report_interval
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.last_report_count = 0

    def report_progress(self, logs_generated: int) -> None:
        """Report progress."""
        current_time = time.time()

        # Report every N logs or every few seconds
        if (
            logs_generated - self.last_report_count >= self.report_interval
            or current_time - self.last_report_time >= 5.0
        ):

            progress_percent = (logs_generated / self.total_logs) * 100
            duration = current_time - self.start_time

            if duration > 0:
                current_rate = logs_generated / duration
                recent_rate = (logs_generated - self.last_report_count) / (
                    current_time - self.last_report_time
                )

                if logs_generated > 0:
                    eta = (self.total_logs - logs_generated) / current_rate
                    eta_str = f"ETA: {eta:.1f}s"
                else:
                    eta_str = "ETA: calculating..."

                print(
                    f"Progress: {logs_generated:,}/{self.total_logs:,} ({progress_percent:.1f}%) "
                    f"| Rate: {current_rate:,.0f}/s (recent: {recent_rate:,.0f}/s) "
                    f"| {eta_str}"
                )

            self.last_report_time = current_time
            self.last_report_count = logs_generated

    def report_completion(self, final_count: int) -> None:
        """Report completion."""
        duration = time.time() - self.start_time
        rate = final_count / duration if duration > 0 else 0

        print(
            f"Generation complete: {final_count:,} logs in {duration:.2f}s "
            f"({rate:,.0f} logs/second)"
        )


class BenchmarkRunner:
    """Run performance benchmarks."""

    @staticmethod
    def run_generation_benchmark(config, iterations: int = 3) -> Dict[str, Any]:
        """Run a generation benchmark."""
        from logforge.core.generator import LogGenerator

        results = []

        for i in range(iterations):
            print(f"Running benchmark iteration {i + 1}/{iterations}")

            generator = LogGenerator(config)
            monitor = PerformanceMonitor()

            start_time = time.time()
            generator.performance_monitor = monitor
            generator.generate()
            end_time = time.time()

            stats = monitor.get_stats()
            stats["iteration"] = i + 1
            stats["wall_time"] = end_time - start_time

            results.append(stats)

        # Calculate averages
        avg_results = {
            "iterations": iterations,
            "avg_duration": sum(r["duration_seconds"] for r in results) / iterations,
            "avg_logs_per_second": sum(r["logs_per_second"] for r in results)
            / iterations,
            "avg_memory_usage": sum(r["peak_memory_usage_mb"] for r in results)
            / iterations,
            "avg_cpu_usage": sum(r["peak_cpu_usage_percent"] for r in results)
            / iterations,
            "min_logs_per_second": min(r["logs_per_second"] for r in results),
            "max_logs_per_second": max(r["logs_per_second"] for r in results),
            "detailed_results": results,
        }

        return avg_results

    @staticmethod
    def format_benchmark_results(results: Dict[str, Any]) -> str:
        """Format benchmark results for display."""
        lines = [
            f"Benchmark Results ({results['iterations']} iterations):",
            f"  Average duration: {results['avg_duration']:.2f} seconds",
            f"  Average logs/second: {results['avg_logs_per_second']:,.0f}",
            f"  Range: {results['min_logs_per_second']:,.0f} - {results['max_logs_per_second']:,.0f} logs/second",
            f"  Average memory usage: {results['avg_memory_usage']:.1f} MB",
            f"  Average CPU usage: {results['avg_cpu_usage']:.1f}%",
        ]

        return "\n".join(lines)
