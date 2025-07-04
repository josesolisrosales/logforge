#!/usr/bin/env python3
"""
Basic usage examples for LogSmith.

This script demonstrates the basic functionality of LogSmith
for generating logs programmatically.
"""

from datetime import timedelta
from pathlib import Path

from logforge import LogGenerator, LogConfig


def basic_example():
    """Generate basic logs with default configuration."""
    print("=== Basic Example ===")
    
    # Create a simple configuration
    config = LogConfig(
        total_logs=1000,
        output={"format": "standard"}
    )
    
    # Generate logs
    generator = LogGenerator(config)
    generator.generate()
    
    # Show performance stats
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} logs in {stats['duration_seconds']:.2f} seconds")
    print(f"Rate: {stats['logs_per_second']:,.0f} logs/second")
    print()


def json_example():
    """Generate JSON logs with custom fields."""
    print("=== JSON Example ===")
    
    config = LogConfig(
        total_logs=5000,
        output={
            "format": "json",
            "file_path": Path("examples/output/app.json")
        },
        custom_fields={
            "app_name": "example-app",
            "version": "1.0.0",
            "environment": "development"
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} JSON logs")
    print(f"Output file: {config.output.file_path}")
    print()


def apache_logs_example():
    """Generate Apache access logs."""
    print("=== Apache Logs Example ===")
    
    config = LogConfig(
        total_logs=10000,
        output={
            "format": "apache_combined",
            "file_path": Path("examples/output/access.log")
        },
        time={
            "duration": timedelta(hours=1),
            "interval": 0.1,  # One log every 100ms
            "jitter": 0.2
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} Apache logs")
    print(f"Output file: {config.output.file_path}")
    print()


def custom_distribution_example():
    """Generate logs with custom level distribution."""
    print("=== Custom Distribution Example ===")
    
    config = LogConfig(
        total_logs=2000,
        log_levels=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        level_distribution={
            "levels": {
                "DEBUG": 0.1,   # 10% debug
                "INFO": 0.7,    # 70% info
                "WARNING": 0.15, # 15% warning
                "ERROR": 0.04,   # 4% error
                "CRITICAL": 0.01 # 1% critical
            }
        },
        output={
            "format": "json",
            "file_path": Path("examples/output/custom_levels.json")
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} logs with custom distribution")
    print(f"Output file: {config.output.file_path}")
    print()


def high_performance_example():
    """Generate a large number of logs with performance optimization."""
    print("=== High Performance Example ===")
    
    config = LogConfig(
        total_logs=100000,  # 100K logs
        output={
            "format": "json",
            "file_path": Path("examples/output/high_performance.json"),
            "compression": "gzip"
        },
        performance={
            "batch_size": 10000,
            "workers": 4,
            "use_numpy": True,
            "precompute_timestamps": True
        }
    )
    
    generator = LogGenerator(config)
    
    # Show estimated time
    estimated_time = generator.estimate_generation_time()
    print(f"Estimated generation time: {estimated_time:.2f} seconds")
    
    # Generate with progress callback
    def progress_callback(percentage, logs_generated):
        if logs_generated % 10000 == 0:
            print(f"Progress: {logs_generated:,} logs ({percentage:.1%})")
    
    generator.generate(progress_callback)
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']:,} logs in {stats['duration_seconds']:.2f} seconds")
    print(f"Rate: {stats['logs_per_second']:,.0f} logs/second")
    print(f"Peak memory usage: {stats['peak_memory_usage_mb']:.1f} MB")
    print(f"Output file: {config.output.file_path}")
    print()


def csv_example():
    """Generate CSV logs for data analysis."""
    print("=== CSV Example ===")
    
    config = LogConfig(
        total_logs=5000,
        output={
            "format": "csv",
            "file_path": Path("examples/output/logs.csv")
        },
        custom_fields={
            "user_id": "12345",
            "session_id": "abcdef",
            "request_id": "req-001"
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} CSV logs")
    print(f"Output file: {config.output.file_path}")
    print()


def syslog_example():
    """Generate syslog format logs."""
    print("=== Syslog Example ===")
    
    config = LogConfig(
        total_logs=3000,
        output={
            "format": "syslog",
            "file_path": Path("examples/output/system.log")
        },
        time={
            "interval": 0.5,  # One log every 500ms
            "jitter": 0.1
        }
    )
    
    generator = LogGenerator(config)
    generator.generate()
    
    stats = generator.get_performance_stats()
    print(f"Generated {stats['total_logs_generated']} syslog entries")
    print(f"Output file: {config.output.file_path}")
    print()


def main():
    """Run all examples."""
    # Create output directory
    Path("examples/output").mkdir(parents=True, exist_ok=True)
    
    print("LogSmith Basic Usage Examples")
    print("=" * 40)
    print()
    
    # Run examples
    basic_example()
    json_example()
    apache_logs_example()
    custom_distribution_example()
    high_performance_example()
    csv_example()
    syslog_example()
    
    print("All examples completed!")
    print("Check the 'examples/output/' directory for generated log files.")


if __name__ == "__main__":
    main()